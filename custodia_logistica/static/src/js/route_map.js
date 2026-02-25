odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // Inicializar con retraso para asegurar carga de librerías
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
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(routeMap);

        // Llamada al controlador portal_route.py
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
                    L.geoJSON(route.geometry, {style: {color: "#3388ff", weight: 6}}).addTo(routeMap);
                    routeMap.fitBounds(L.geoJSON(route.geometry).getBounds());
                    
                    var infoDiv = document.getElementById('route_info');
                    if (infoDiv) {
                        var dist = (route.distance / 1000).toFixed(1);
                        var dur = Math.floor(route.duration / 3600) + "h " + Math.round((route.duration % 3600) / 60) + "m";
                        infoDiv.innerHTML = "<strong>Distancia:</strong> " + dist + " km | <strong>Tiempo:</strong> " + dur;
                        infoDiv.style.display = "block";
                    }
                }
            });
        });
    }

    function initLiveMap() {
        var liveCont = document.getElementById('live_map');
        if (!liveCont) return;

        var liveMap = L.map('live_map').setView([19.43, -99.13], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(liveMap);
        var marker = L.marker([19.43, -99.13]).addTo(liveMap);

        function update() {
            fetch("/mis-servicios/" + liveCont.dataset.serviceId + "/tracking", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: { access_token: liveCont.dataset.token } })
            }).then(res => res.json()).then(d => {
                var r = d.result || d;
                if (r.lat && r.lng) {
                    marker.setLatLng([r.lat, r.lng]);
                    liveMap.panTo([r.lat, r.lng]);
                }
            });
        }
        update(); setInterval(update, 15000);
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
