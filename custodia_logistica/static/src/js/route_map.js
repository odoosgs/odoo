(function () {
    "use strict";

    console.log("Custodia Logística: Iniciando carga de mapas duales...");

    document.addEventListener("DOMContentLoaded", function () {
        // Ejecutamos la inicialización con un pequeño retraso
        setTimeout(() => {
            initAllMaps();
        }, 500);
    });

    async function initAllMaps() {
        // --- 1. MAPA DE RUTA PLANEADA ---
        const routeContainer = document.getElementById("route-map");
        if (routeContainer && routeContainer.dataset.rutaId) {
            await drawPlannedRoute(routeContainer.dataset.rutaId);
        }

        // --- 2. MAPA DE MONITOREO EN VIVO ---
        const liveContainer = document.getElementById("live-map");
        if (liveContainer) {
            initLiveTracking(liveContainer);
        }
    }

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
            // Crear instancia única para el mapa de ruta
            const mapRoute = L.map("route-map").setView(origin, 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            const path = coords.map(p => [p.lat, p.lng]);
            L.polyline(path, { color: "blue", weight: 5 }).addTo(mapRoute);
            mapRoute.fitBounds(L.polyline(path).getBounds());
            
            setTimeout(() => mapRoute.invalidateSize(), 200);
        } catch (e) { console.error("Error Ruta Planeada:", e); }
    }

    function initLiveTracking(container) {
        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;
        
        // Crear instancia única para el mapa en vivo (CDMX por defecto)
        const mapLive = L.map('live-map').setView([19.4326, -99.1332], 5);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
        
        let marker = L.marker([19.4326, -99.1332]).addTo(mapLive);

        async function update() {
            try {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos);
                    mapLive.panTo(pos);
                }
            } catch (e) { console.error("Error Live Update:", e); }
        }
        
        setTimeout(() => {
            mapLive.invalidateSize();
            update();
        }, 400);
        setInterval(update, 20000);
    }

    // Mantener tus escuchadores de clics e incidencias aquí abajo...
    document.addEventListener("click", async function (e) {
        if (e.target.matches("#btn-llegada")) { /* ... código de llegada ... */ }
        // ... resto de botones e incidencias ...
    });
})();
