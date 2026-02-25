odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    document.addEventListener("DOMContentLoaded", function () {
        // Pequeño retardo para asegurar que Leaflet esté en el DOM
        setTimeout(function() {
            initRouteMap();
            initLiveMap();
            initCustodioActions();
        }, 500);
    });

    function initRouteMap() {
        var mapContainer = document.getElementById('route_map');
        if (!mapContainer || !mapContainer.dataset.rutaId) return;

        var routeMap = L.map('route_map').setView([19.4326, -99.1332], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(routeMap);

        // FETCH robusto al controlador de rutas
        fetch('/custodia/ruta/' + mapContainer.dataset.rutaId + '/coordinates', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(res => res.json())
        .then(data => {
            var points = data.result;
            if (!points || points.length < 2) return;

            var coords = points.map(p => p.lng + "," + p.lat).join(";");
            fetch("https://router.project-osrm.org/route/v1/driving/" + coords + "?overview=full&geometries=geojson")
            .then(res => res.json())
            .then(osrm => {
                if (osrm.routes && osrm.routes.length) {
                    var route = osrm.routes[0];
                    var geojson = L.geoJSON(route.geometry, {style: {color: "blue", weight: 5}}).addTo(routeMap);
                    routeMap.fitBounds(geojson.getBounds());
                    
                    // Inyectar métricas en el div correspondiente
                    var infoDiv = document.getElementById('route_info');
                    if (infoDiv) {
                        var dist = (route.distance / 1000).toFixed(2);
                        var dur = Math.round(route.duration / 60);
                        infoDiv.innerHTML = "<strong>Distancia:</strong> " + dist + " km | <strong>Tiempo:</strong> " + Math.floor(dur/60) + "h " + (dur%60) + "min";
                        infoDiv.style.display = "block";
                    }
                }
            });
        });
    }

    function initLiveMap() {
        var liveContainer = document.getElementById('live_map');
        if (!liveContainer) return;

        var liveMap = L.map('live_map').setView([19.43, -99.13], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(liveMap);
        var marker = L.marker([19.43, -99.13]).addTo(liveMap);

        function update() {
            fetch("/mis-servicios/" + liveContainer.dataset.serviceId + "/tracking", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: { access_token: liveContainer.dataset.token } })
            })
            .then(res => res.json())
            .then(data => {
                var r = data.result || data;
                if (r.lat && r.lng) {
                    marker.setLatLng([r.lat, r.lng]);
                    liveMap.panTo([r.lat, r.lng]);
                }
            });
        }
        update();
        setInterval(update, 15000);
    }

    function initCustodioActions() {
        document.addEventListener("click", function (e) {
            var btn = e.target.closest(".btn-custodio-action");
            if (!btn) return;
            fetch("/custodia/service/" + btn.dataset.serviceId + "/" + btn.dataset.action, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            }).then(() => location.reload());
        });
    }
});
