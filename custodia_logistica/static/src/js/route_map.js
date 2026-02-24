odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    document.addEventListener("DOMContentLoaded", function () {

        var mapContainer = document.getElementById('route_map');
        if (!mapContainer) {
            return;
        }

        var rutaId = mapContainer.dataset.rutaId;

        var routeMap = L.map('route_map').setView([23.6345, -102.5528], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(routeMap);

        ajax.jsonRpc('/custodia/ruta/' + rutaId + '/coordinates', 'call', {})
            .then(function (data) {

                if (!data || !data.length) {
                    return;
                }

                var points = data;

                var startPoint = points[0];
                var endPoint = points[points.length - 1];

                // 🔵 Solicitar ruta real a OSRM
                var osrmUrl = "https://router.project-osrm.org/route/v1/driving/" +
                    startPoint.lng + "," + startPoint.lat + ";" +
                    endPoint.lng + "," + endPoint.lat +
                    "?overview=full&geometries=geojson";

                fetch(osrmUrl)
                    .then(response => response.json())
                    .then(function (osrm) {

                        if (!osrm.routes || !osrm.routes.length) {
                            return;
                        }

                        var route = osrm.routes[0];

                        // 🔵 Dibujar línea azul
                        var geojson = L.geoJSON(route.geometry, {
                            style: {
                                color: "blue",
                                weight: 5
                            }
                        }).addTo(routeMap);

                        routeMap.fitBounds(geojson.getBounds());

                        // 🟢 Marcador inicio
                        L.circleMarker([startPoint.lat, startPoint.lng], {
                            color: 'green',
                            radius: 8,
                            fillColor: 'green',
                            fillOpacity: 1
                        }).addTo(routeMap).bindPopup("Inicio");

                        // 🔴 Marcador fin
                        L.circleMarker([endPoint.lat, endPoint.lng], {
                            color: 'red',
                            radius: 8,
                            fillColor: 'red',
                            fillOpacity: 1
                        }).addTo(routeMap).bindPopup("Destino");

                        // 📏 Distancia y tiempo
                        var distanceKm = (route.distance / 1000).toFixed(2);

                        var totalMinutes = Math.round(route.duration / 60);
                        var hours = Math.floor(totalMinutes / 60);
                        var minutes = totalMinutes % 60;

                        var timeFormatted = hours > 0
                            ? hours + " h " + minutes + " min"
                            : minutes + " min";

                        var infoDiv = document.getElementById('route_info');
                        if (infoDiv) {
                            infoDiv.innerHTML =
                                "<strong>Distancia:</strong> " + distanceKm + " km | " +
                                "<strong>Tiempo:</strong> " + timeFormatted;
                        }

                    });

            });

    });

});
