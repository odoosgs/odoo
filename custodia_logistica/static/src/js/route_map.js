(function () {
    "use strict";

    // =========================================================
    // 1. ARRANCAR MAPAS AL CARGAR LA PÁGINA
    // =========================================================
    document.addEventListener("DOMContentLoaded", function () {
        console.log("DOM listo - Verificando existencia de mapas...");

        setTimeout(() => {
            const routeMapContainer = document.getElementById("route-map");
            const liveMapContainer = document.getElementById("live-map");

            if (routeMapContainer) {
                console.log("Iniciando Mapa de Ruta Planeada...");
                initPlannedRouteMap(routeMapContainer);
            }

            if (liveMapContainer) {
                console.log("Iniciando Mapa de Monitoreo en Vivo...");
                initLiveTrackingMap(liveMapContainer);
            }
        }, 500);
    });

    // =========================================================
    // 2. LÓGICA DE FILTRADO DE SELECTORES (FORMULARIO)
    // =========================================================
    document.addEventListener("change", async function (e) {
        if (e.target && e.target.id === "ruta_maestra_id") {
            const maestraId = e.target.value;
            const origenSelect = document.getElementById("nodo_origen_id");
            const destinoSelect = document.getElementById("nodo_destino_id");

            if (!maestraId || !origenSelect || !destinoSelect) return;

            try {
                const response = await fetch(`/get_nodos_by_maestra/${maestraId}`);
                if (!response.ok) return;
                const result = await response.json();

                origenSelect.innerHTML = '<option value="">-- Seleccione salida --</option>';
                result.origenes.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id; opt.textContent = n.name;
                    origenSelect.appendChild(opt);
                });

                destinoSelect.innerHTML = '<option value="">-- Seleccione llegada --</option>';
                result.destinos.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id; opt.textContent = n.name;
                    destinoSelect.appendChild(opt);
                });

                origenSelect.disabled = false;
                destinoSelect.disabled = false;
                origenSelect.removeAttribute('disabled');
                destinoSelect.removeAttribute('disabled');
            } catch (err) {
                console.error("Error en el filtrado:", err);
            }
        }
    });

    // =========================================================
    // 3. FUNCIÓN: MAPA 1 - RUTA PLANEADA
    // =========================================================
    async function initPlannedRouteMap(container) {
        const rutaId = container.dataset.rutaId;
        if (!rutaId) return;

        try {
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });

            const data = await response.json();
            const coords = data.result;

            if (!coords || coords.length < 2) return;

            const origin = coords[0];
            const destination = coords[coords.length - 1];

            const mapRoute = L.map("route-map").setView([origin.lat, origin.lng], 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            // Dibujo de ruta por carretera vía OSRM
            const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`;
            const routeResponse = await fetch(osrmUrl);
            const routeData = await routeResponse.json();

            if (routeData.routes && routeData.routes.length > 0) {
                const routeLayer = L.geoJSON(routeData.routes[0].geometry, {
                    style: { color: "blue", weight: 5 }
                }).addTo(mapRoute);
                mapRoute.fitBounds(routeLayer.getBounds());
                
                // Actualizar resumen
                const distanceKm = (routeData.routes[0].distance / 1000).toFixed(1);
                if (document.getElementById("route-distance")) {
                    document.getElementById("route-distance").textContent = distanceKm + " km";
                }
            }
        } catch (e) { console.error("Error Mapa Ruta:", e); }
    }

    // =========================================================
    // 4. FUNCIÓN: MAPA 2 - MONITOREO EN VIVO
    // =========================================================
    async function initLiveTrackingMap(container) {
        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;

        try {
            // Inicializamos el mapa. Leaflet necesita un centro inicial.
            const mapLive = L.map("live-map").setView([23.6345, -102.5528], 5); // Centro de México
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
            const marker = L.marker([23.6345, -102.5528]).addTo(mapLive);

            async function update() {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos);
                    mapLive.panTo(pos);
                    if (mapLive.getZoom() < 10) mapLive.setZoom(13);
                }
            }
            update();
            setInterval(update, 30000);
        } catch (e) { console.error("Error Mapa Vivo:", e); }
    }
})();
