/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {
    // 1. Inicializar Mapa de Ruta Planeada (Izquierda)
    initRouteMap();
    // 2. Inicializar Mapa en Vivo (Derecha)
    initLiveMap();
    // 3. Inicializar Botones de Acción
    initCustodioActions();
});

/* ============================================================
    MAPA DE RUTA PLANEADA
============================================================ */
function initRouteMap() {
    var mapContainer = document.getElementById('route_map');
    if (!mapContainer) return;

    var rutaId = mapContainer.dataset.rutaId;
    if (!rutaId) return;

    var routeMap = L.map('route_map').setView([19.4326, -99.1332], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(routeMap);

    fetch('/custodia/ruta/' + rutaId + '/coordinates', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params: {} })
    })
    .then(res => res.json())
    .then(response => {
        var points = response.result;
        if (!points || points.length < 2) return;

        // OSRM para dibujo sobre carretera
        var coords = points.map(p => p.lng + "," + p.lat).join(";");
        fetch("https://router.project-osrm.org/route/v1/driving/" + coords + "?overview=full&geometries=geojson")
        .then(res => res.json())
        .then(osrm => {
            if (osrm.routes && osrm.routes.length) {
                var route = osrm.routes[0];
                var geojson = L.geoJSON(route.geometry, { style: { color: "#3388ff", weight: 6 } }).addTo(routeMap);
                routeMap.fitBounds(geojson.getBounds());
                
                // Actualizar métricas en el div route_info
                var infoDiv = document.getElementById('route_info');
                if (infoDiv) {
                    var dist = (route.distance / 1000).toFixed(1);
                    var dur = Math.floor(route.duration / 3600) + "h " + Math.round((route.duration % 3600) / 60) + "m";
                    infoDiv.innerHTML = `<strong>Distancia:</strong> ${dist} km | <strong>Tiempo:</strong> ${dur}`;
                    infoDiv.style.display = "block";
                }
            }
        });
    });
}

/* ============================================================
    MONITOREO EN VIVO
============================================================ */
function initLiveMap() {
    var liveContainer = document.getElementById('live_map');
    if (!liveContainer) return;

    var serviceId = liveContainer.dataset.serviceId;
    var token = liveContainer.dataset.token;

    var liveMap = L.map('live_map').setView([19.4326, -99.1332], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(liveMap);
    var marker = L.marker([19.4326, -99.1332]).addTo(liveMap);

    function update() {
        fetch("/mis-servicios/" + serviceId + "/tracking", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: { access_token: token } })
        }).then(res => res.json()).then(data => {
            var res = data.result || data;
            if (res.lat && res.lng) {
                marker.setLatLng([res.lat, res.lng]);
                liveMap.panTo([res.lat, res.lng]);
            }
        });
    }
    update();
    setInterval(update, 20000);
}

/* ============================================================
    ACCIONES DEL CUSTODIO (BOTONES)
============================================================ */
function initCustodioActions() {
    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".btn-custodio-action");
        if (!btn) return;

        var serviceId = btn.dataset.serviceId;
        var action = btn.dataset.action;

        fetch("/custodia/service/" + serviceId + "/" + action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        }).then(() => location.reload());
    });
}
