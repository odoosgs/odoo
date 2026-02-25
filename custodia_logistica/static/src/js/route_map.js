odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var domReady = require('web.dom_ready');

    domReady(function () {
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

        if (typeof L === "undefined") {
            console.error("Leaflet no está cargado.");
            return;
        }

        var routeMap = L.map('route_map').setView([23.6345, -102.5528], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(routeMap);

        ajax.jsonRpc('/custodia/ruta/' + rutaId + '/coordinates', 'call', {})
            .then(function (response) {

                var points = response.result || response;

                if (!points || !Array.isArray(points) || points.length < 2) {
                    console.warn("No hay coordenadas suficientes.");
                    return;
                }

                drawRoute(routeMap, points);
            });
    }

    function drawRoute(routeMap, points) {

        var validPoints = points.filter(function (p) {
            return p && p.lat && p.lng;
        });

        if (validPoints.length < 2) {
            return;
        }

        var coords = validPoints
            .map(function (p) {
                return p.lng + "," + p.lat;
            })
            .join(";");

        var osrmUrl =
            "https://router.project-osrm.org/route/v1/driving/" +
            coords +
            "?overview=full&geometries=geojson";

        fetch(osrmUrl)
            .then(function (response) {
                return response.json();
            })
            .then(function (osrm) {

                if (!osrm.routes || !osrm.routes.length) {
                    return;
                }

                var route = osrm.routes[0];

                var geojson = L.geoJSON(route.geometry, {
                    style: {
                        color: "#003366",
                        weight: 5
                    }
                }).addTo(routeMap);

                routeMap.fitBounds(geojson.getBounds());

                updateRouteInfo(route);
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
       ACCIONES CUSTODIO
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
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(function () {
            location.reload();
        });
    }

});
