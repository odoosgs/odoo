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

            // 1. CREAR EL MAPA INMEDIATAMENTE
            const origin = [coords[0].lat, coords[0].lng];
            const dest = [coords[coords.length - 1].lat, coords[coords.length - 1].lng];
            const mapRoute = L.map("route-map").setView(origin, 6);
            
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap"
            }).addTo(mapRoute);

            // 2. PONER MARCADORES BÁSICOS (Para que el mapa no esté vacío)
            L.marker(origin).addTo(mapRoute).bindPopup("Origen");
            L.marker(dest).addTo(mapRoute).bindPopup("Destino");

            // 3. PEDIR RUTA A OSRM (En segundo plano)
            const osrmCoords = coords.map(p => p.lng + "," + p.lat).join(";");
            
            fetch(`https://router.project-osrm.org/route/v1/driving/${osrmCoords}?overview=full&geometries=geojson`)
                .then(res => res.json())
                .then(osrmData => {
                    if (osrmData.routes && osrmData.routes.length > 0) {
                        const routeGeo = L.geoJSON(osrmData.routes[0].geometry, {
                            style: { color: "blue", weight: 5, opacity: 0.8 }
                        }).addTo(mapRoute);
                        
                        mapRoute.fitBounds(routeGeo.getBounds());
                        
                        // Actualizar textos si existen
                        if(document.getElementById("route-distance")) {
                            document.getElementById("route-distance").innerText = (osrmData.routes[0].distance / 1000).toFixed(2) + " km";
                        }
                    } else {
                        // Respaldo si falla OSRM: Línea recta
                        const simplePath = coords.map(p => [p.lat, p.lng]);
                        L.polyline(simplePath, {color: 'blue', weight: 4, dashArray: '5, 10'}).addTo(mapRoute);
                    }
                })
                .catch(err => console.error("OSRM Error:", err));

            // Forzar renderizado
            setTimeout(() => mapRoute.invalidateSize(), 300);

        } catch (e) { console.error("Error crítico:", e); }
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
