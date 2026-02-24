odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    document.addEventListener("DOMContentLoaded", function () {

        initRouteMap();
        initCustodioActions();

    });

    /* ============================================================
       MAPA DE RUTA
    ============================================================ */

    function initRouteMap() {

        var mapContainer = document.getElementById('route_map');
        if (!mapContainer) {
            return;
        }

        var rutaId = mapContainer.dataset.rutaId;
        if (!rutaId) {
            return;
        }

        var routeMap = L.map('route_map').setView([23.6345, -102.5528], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(routeMap);

        ajax.jsonRpc('/custodia/ruta/' + rutaId + '/coordinates', 'call', {})
            .then(function (data) {

                if (!data || !data.length) {
                    console.warn("No hay coordenadas para la ruta.");
                    return;
                }

                drawRoute(routeMap, data);

            })
            .catch(function (error) {
                console.error("Error obteniendo coordenadas:", error);
            });
    }

    function drawRoute(routeMap, points) {

        var startPoint = points[0];
        var endPoint = points[points.length - 1];

        if (!startPoint || !endPoint) {
            return;
        }

        var osrmUrl =
            "https://router.project-osrm.org/route/v1/driving/" +
            startPoint.lng + "," + startPoint.lat + ";" +
            endPoint.lng + "," + endPoint.lat +
            "?overview=full&geometries=geojson";

        fetch(osrmUrl)
            .then(function (response) {
                return response.json();
            })
            .then(function (osrm) {

                if (!osrm.routes || !osrm.routes.length) {
                    console.warn("OSRM no devolvió rutas.");
                    return;
                }

                var route = osrm.routes[0];

                // Línea azul
                var geojson = L.geoJSON(route.geometry, {
                    style: {
                        color: "blue",
                        weight: 5
                    }
                }).addTo(routeMap);

                routeMap.fitBounds(geojson.getBounds());

                // Marcador inicio (verde)
                L.circleMarker([startPoint.lat, startPoint.lng], {
                    color: 'green',
                    radius: 8,
                    fillColor: 'green',
                    fillOpacity: 1
                }).addTo(routeMap).bindPopup("Inicio");

                // Marcador fin (rojo)
                L.circleMarker([endPoint.lat, endPoint.lng], {
                    color: 'red',
                    radius: 8,
                    fillColor: 'red',
                    fillOpacity: 1
                }).addTo(routeMap).bindPopup("Destino");

                updateRouteInfo(route);

            })
            .catch(function (error) {
                console.error("Error consultando OSRM:", error);
            });
    }

    function updateRouteInfo(route) {

        var infoDiv = document.getElementById('route_info');
        if (!infoDiv) {
            return;
        }

        var distanceKm = (route.distance / 1000).toFixed(2);

        var totalMinutes = Math.round(route.duration / 60);
        var hours = Math.floor(totalMinutes / 60);
        var minutes = totalMinutes % 60;

        var timeFormatted = hours > 0
            ? hours + " h " + minutes + " min"
            : minutes + " min";

        infoDiv.innerHTML =
            "<strong>Distancia:</strong> " + distanceKm + " km | " +
            "<strong>Tiempo:</strong> " + timeFormatted;
    }


    /* ============================================================
       ACCIONES CUSTODIO (Botones Portal)
    ============================================================ */

    function initCustodioActions() {

        document.addEventListener("click", function (e) {

            if (e.target.matches("#btn-en-ruta")) {
                executeAction(e.target.dataset.serviceId, "en_ruta");
            }

            if (e.target.matches("#btn-llegada")) {
                executeAction(e.target.dataset.serviceId, "llegada");
            }

            if (e.target.matches("#btn-iniciar-servicio")) {
                executeAction(e.target.dataset.serviceId, "iniciar");
            }

        });
    }

    function executeAction(serviceId, action) {

        if (!serviceId || !action) {
            return;
        }

        fetch("/custodia/service/" + serviceId + "/" + action, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ params: {} })
        })
        .then(function (res) {
            return res.json();
        })
        .then(function () {
            location.reload();
        })
        .catch(function (error) {
            console.error("Error ejecutando acción:", error);
        });
    }

});
