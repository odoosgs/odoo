(function () {
    "use strict";

    console.log("Custodia Logística: Iniciando carga de mapas duales...");

    document.addEventListener("DOMContentLoaded", function () {
        // Ejecutamos la carga con un retraso escalonado para evitar conflictos
        setTimeout(() => {
            initPlannedRouteMap();
        }, 300);

        setTimeout(() => {
            initLiveTrackingMap();
        }, 800);
    });

    // --- 1. FUNCIÓN MAPA RUTA PLANEADA ---
    async function drawPlannedRoute(rutaId) {
        try {
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });
            const data = await response.json();
            const coords = data.result;

            if (!coords || coords.length < 2) return;

            const origin = [coords[0].lat, coords[0].lng];
            const mapRoute = L.map("route-map").setView(origin, 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            // Marcadores de Origen y Destino
            coords.forEach(p => {
                let color = p.type === 'origin' ? 'green' : (p.type === 'destination' ? 'red' : 'blue');
                L.circleMarker([p.lat, p.lng], {radius: 7, color: color, fillOpacity: 1}).addTo(mapRoute);
            });

            // --- LLAMADA A OSRM PARA CARRETERA REAL ---
            // Formato requerido: lng,lat;lng,lat
            const osrmCoords = coords.map(p => p.lng + "," + p.lat).join(";");
            
            fetch(`https://router.project-osrm.org/route/v1/driving/${osrmCoords}?overview=full&geometries=geojson`)
                .then(res => res.json())
                .then(osrmData => {
                    if (osrmData.routes && osrmData.routes.length > 0) {
                        // Dibujamos la geometría de la carretera real
                        const routeGeo = L.geoJSON(osrmData.routes[0].geometry, {
                            style: { color: "blue", weight: 5, opacity: 0.7 }
                        }).addTo(mapRoute);
                        
                        mapRoute.fitBounds(routeGeo.getBounds());

                        // Actualizar etiquetas de distancia y tiempo (opcional si tienes los IDs en el HTML)
                        const distElem = document.getElementById("route-distance");
                        const durElem = document.getElementById("route-duration");
                        if(distElem) distElem.innerText = (osrmData.routes[0].distance / 1000).toFixed(2) + " km";
                        if(durElem) durElem.innerText = Math.round(osrmData.routes[0].duration / 60) + " min";
                    } else {
                        // Respaldo: Si falla OSRM, dibujamos línea recta
                        const fallbackPath = coords.map(p => [p.lat, p.lng]);
                        const poly = L.polyline(fallbackPath, {color: 'red', weight: 3, dashArray: '5, 10'}).addTo(mapRoute);
                        mapRoute.fitBounds(poly.getBounds());
                    }
                });
            
            setTimeout(() => mapRoute.invalidateSize(), 200);
        } catch (e) { console.error("Error Ruta Planeada:", e); }
    }

    // --- 2. FUNCIÓN MAPA MONITOREO EN VIVO ---
    function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;
        
        // Instancia única para el mapa en vivo
        const mapLive = L.map('live-map').setView([19.4326, -99.1332], 5);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
        
        let marker = L.marker([19.4326, -99.1332]).addTo(mapLive).bindPopup("Esperando señal...");

        async function updatePos() {
            try {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos).setPopupContent("Última actualización: " + (data.last_update || "Reciente"));
                    mapLive.panTo(pos);
                }
            } catch (e) { console.error("Error en Actualización en Vivo:", e); }
        }
        
        setTimeout(() => {
            mapLive.invalidateSize();
            updatePos();
        }, 300);
        
        // Actualización cada 30 segundos para no saturar el servidor
        setInterval(updatePos, 30000);
    }
})();
