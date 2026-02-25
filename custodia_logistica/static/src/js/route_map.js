odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    document.addEventListener("DOMContentLoaded", function () {

        initPlannedRoute();
        initLiveTracking();
        initCustodioActions();

    });

    /* ============================================================
       RUTA PLANEADA (OSRM)
    ============================================================ */

    function initPlannedRoute() {

        var routeContainer = document.getElementById("route-map");
        if (!routeContainer || !routeContainer.dataset.rutaId) {
            return;
        }

        var rutaId = routeContainer.dataset.rutaId;

        fetch("/custodia/ruta/" + rutaId + "/coordinates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(res => res.json())
        .then(function (response) {

            if (!response.result || !response.result.length) {
                console.warn("No hay coordenadas para la ruta.");
                return;
            }

            var points = response.result;
            var firstPoint = points[0];

            var routeMap = L.map("route-map")
                .setView([firstPoint.lat, firstPoint.lng], 6);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap"
            }).addTo(routeMap);

            // Marcadores
            points.forEach(function(p) {

                var color = "blue";
                if (p.type === "origin") color = "green";
                if (p.type === "destination") color = "red";

                L.circleMarker([p.lat, p.lng], {
                    radius: 6,
                    color: color,
                    fillColor: color,
                    fillOpacity: 1
                }).addTo(routeMap);
            });

            // Construir string OSRM
            var coords = points.map(p => p.lng + "," + p.lat).join(";");

            fetch("https://router.project-osrm.org/route/v1/driving/" +
                  coords + "?overview=full&geometries=geojson")
            .then(res => res.json())
            .then(function(osrmData) {

                if (!osrmData.routes || !osrmData.routes.length) {
                    return;
                }

                var routeData = osrmData.routes[0];

                var geojsonLayer = L.geoJSON(routeData.geometry, {
                    style: {
                        color: "#003366",
                        weight: 5
                    }
                }).addTo(routeMap);

                routeMap.fitBounds(geojsonLayer.getBounds());

                updateRouteSummary(routeData);

            });

        });
    }

    function updateRouteSummary(routeData) {

        var summary = document.getElementById("route-summary");
        if (!summary) return;

        var distanceKm = (routeData.distance / 1000).toFixed(2);
        var totalMinutes = Math.round(routeData.duration / 60);
        var hours = Math.floor(totalMinutes / 60);
        var minutes = totalMinutes % 60;

        var formattedDuration = "";
        if (hours > 0) formattedDuration += hours + " h ";
        formattedDuration += minutes + " min";

        document.getElementById("route-distance").innerText = distanceKm + " km";
        document.getElementById("route-duration").innerText = formattedDuration;

        summary.style.display = "block";
    }

    /* ============================================================
       MONITOREO EN VIVO (endpoint HTTP nuevo)
    ============================================================ */

    function initLiveTracking() {

        var liveContainer = document.getElementById("live-map");
        if (!liveContainer) return;

        var serviceId = liveContainer.dataset.serviceId;
        var token = liveContainer.dataset.token;

        if (!serviceId || !token) return;

        var liveMap = L.map('live-map').setView([19.4326, -99.1332], 6);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap"
        }).addTo(liveMap);

        var marker = L.marker([19.4326, -99.1332]).addTo(liveMap);

        function updateLocation() {

            fetch("/mis-servicios/" + serviceId +
                  "/tracking?access_token=" + token, {
                method: "GET"
            })
            .then(res => res.json())
            .then(function(data) {

                if (!data.lat || !data.lng) return;

                var newLatLng = [parseFloat(data.lat), parseFloat(data.lng)];

                marker.setLatLng(newLatLng);
                liveMap.panTo(newLatLng);

            });
        }

        updateLocation();
        setInterval(updateLocation, 15000);
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

        if (!serviceId || !action) return;

        fetch("/custodia/service/" + serviceId + "/" + action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(res => res.json())
        .then(function () {
            location.reload();
        });
    }

});
