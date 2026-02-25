odoo.define('custodia_logistica.route_map', function (require) {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        initRouteMap();
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

        // Inicializar el mapa
        var routeMap = L.map('route_map').setView([19.4326, -99.1332], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(routeMap);

        // Llamada al controlador para obtener coordenadas de la ruta
        fetch('/custodia/ruta/' + rutaId + '/coordinates', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(res => res.json())
        .then(response => {
            var points = response.result;
            if (!points || !Array.isArray(points) || points.length < 2) {
                console.warn("No hay coordenadas suficientes para pintar la ruta.");
                return;
            }
            drawRoute(routeMap, points);
        })
        .catch(err => console.error("Error obteniendo coordenadas:", err));
    }

    function drawRoute(routeMap, points) {
        var startPoint = points[0];
        var endPoint = points[points.length - 1];

        if (!startPoint || !endPoint) return;

        // Construir string para OSRM (lng,lat)
        var coords = points.map(p => p.lng + "," + p.lat).join(";");
        var osrmUrl = "https://router.project-osrm.org/route/v1/driving/" + 
                      coords + "?overview=full&geometries=geojson";

        fetch(osrmUrl)
            .then(res => res.json())
            .then(osrm => {
                if (!osrm.routes || !osrm.routes.length) {
                    console.warn("OSRM no devolvió rutas.");
                    return;
                }

                var route = osrm.routes[0];

                // Dibujar línea de la carretera
                var geojson = L.geoJSON(route.geometry, {
                    style: { color: "#3388ff", weight: 6, opacity: 0.8 }
                }).addTo(routeMap);

                routeMap.fitBounds(geojson.getBounds());

                // Marcador inicio (verde)
                L.circleMarker([startPoint.lat, startPoint.lng], {
                    color: 'green', radius: 8, fillColor: 'green', fillOpacity: 1
                }).addTo(routeMap).bindPopup("Inicio");

                // Marcador fin (rojo)
                L.circleMarker([endPoint.lat, endPoint.lng], {
                    color: 'red', radius: 8, fillColor: 'red', fillOpacity: 1
                }).addTo(routeMap).bindPopup("Destino");

                updateRouteInfo(route);
            })
            .catch(err => console.error("Error consultando OSRM:", err));
    }

    function updateRouteInfo(route) {
        var infoDiv = document.getElementById('route_info');
        if (!infoDiv) return;

        var distanceKm = (route.distance / 1000).toFixed(2);
        var totalMinutes = Math.round(route.duration / 60);
        var hours = Math.floor(totalMinutes / 60);
        var minutes = totalMinutes % 60;

        var timeFormatted = hours > 0 ? hours + " h " + minutes + " min" : minutes + " min";

        infoDiv.innerHTML = "<strong>Distancia:</strong> " + distanceKm + " km | " +
                           "<strong>Tiempo estimado:</strong> " + timeFormatted;
        infoDiv.style.display = "block";
    }

    /* ============================================================
        ACCIONES CUSTODIO (Botones)
    ============================================================ */
    function initCustodioActions() {
        document.addEventListener("click", function (e) {
            var serviceId = e.target.dataset.serviceId;
            if (!serviceId) return;

            if (e.target.matches("#btn-en-ruta")) executeAction(serviceId, "en_ruta");
            if (e.target.matches("#btn-llegada")) executeAction(serviceId, "llegada");
            if (e.target.matches("#btn-iniciar-servicio")) executeAction(serviceId, "iniciar");
        });
    }

    function executeAction(serviceId, action) {
        fetch("/custodia/service/" + serviceId + "/" + action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        })
        .then(res => res.json())
        .then(() => location.reload())
        .catch(err => console.error("Error ejecutando acción:", err));
    }
});
