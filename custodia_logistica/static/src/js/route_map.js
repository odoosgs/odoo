(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // Ejecución escalonada: le damos tiempo al DOM de Odoo para respirar
        setTimeout(() => { initPlannedRouteMap(); }, 200);
        setTimeout(() => { initLiveTrackingMap(); }, 600);
    });

    // --- MAPA 1: RUTA PLANEADA (El código que te funcionó) ---
    async function initPlannedRouteMap() {
        const container = document.getElementById("route-map");
        if (!container || !container.dataset.rutaId) return;

        try {
            const response = await fetch("/custodia/ruta/" + container.dataset.rutaId + "/coordinates", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });
            const data = await response.json();
            const coords = data.result;
            if (!coords || coords.length < 2) return;

            const mapRoute = L.map("route-map").setView([coords[0].lat, coords[0].lng], 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            const path = coords.map(p => [p.lat, p.lng]);
            const polyline = L.polyline(path, { color: "blue", weight: 5 }).addTo(mapRoute);
            mapRoute.fitBounds(polyline.getBounds());
            
            setTimeout(() => mapRoute.invalidateSize(), 200);
        } catch (e) { console.error("Error Mapa Ruta:", e); }
    }

    // --- MAPA 2: MONITOREO EN VIVO (Misma estrategia robusta) ---
    async function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;

        try {
            // Inicialización base
            const mapLive = L.map("live-map").setView([19.4326, -99.1332], 5);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
            
            const marker = L.marker([19.4326, -99.1332]).addTo(mapLive);

            async function update() {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos).bindPopup("Última actualización: " + data.last_update).openPopup();
                    mapLive.panTo(pos);
                }
            }

            setTimeout(() => { mapLive.invalidateSize(); update(); }, 200);
            setInterval(update, 30000); // Actualiza cada 30 seg
        } catch (e) { console.error("Error Mapa Vivo:", e); }
    }
})();
