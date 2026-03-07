(function () {
    "use strict";

    console.log("Archivo route_map.js detectado por el navegador");

// --- LÓGICA DE FILTRADO DE ALTA DISPONIBILIDAD ---
    document.addEventListener("change", async function (e) {
        // Verificamos si el elemento que cambió es nuestro selector de ruta
        if (e.target && e.target.id === "ruta_maestra_id") {
            const maestraId = e.target.value;
            const origenSelect = document.getElementById("nodo_origen_id");
            const destinoSelect = document.getElementById("nodo_destino_id");

            console.log("Detectado cambio en Ruta Maestra (Delegado). ID:", maestraId);

            if (!maestraId || !origenSelect || !destinoSelect) return;

            try {
                const response = await fetch(`/get_nodos_by_maestra/${maestraId}`);
                if (!response.ok) return;

                const result = await response.json();
                console.log("Datos para llenar selectores:", result);

                // Llenar Origen
                origenSelect.innerHTML = '<option value="">-- Seleccione salida --</option>';
                result.origenes.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id;
                    opt.textContent = n.name;
                    origenSelect.appendChild(opt);
                });

                // Llenar Destino
                destinoSelect.innerHTML = '<option value="">-- Seleccione llegada --</option>';
                result.destinos.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id;
                    opt.textContent = n.name;
                    destinoSelect.appendChild(opt);
                });

                // ACTIVACIÓN FÍSICA
                origenSelect.disabled = false;
                destinoSelect.disabled = false;
                origenSelect.removeAttribute('disabled');
                destinoSelect.removeAttribute('disabled');
                
                console.log("Selectores habilitados y con datos.");

            } catch (err) {
                console.error("Error en cascada:", err);
            }
        }
    });
    
    // --- MAPA 1: RUTA PLANEADA ---
    async function initPlannedRouteMap() {
        const container = document.getElementById("route-map");
        if (!container || !container.dataset.rutaId) return;

        const rutaId = container.dataset.rutaId;

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

            const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`;

            const routeResponse = await fetch(osrmUrl);
            const routeData = await routeResponse.json();

            if (!routeData.routes || routeData.routes.length === 0) return;

            const route = routeData.routes[0];
            const routeGeo = route.geometry;

            const mapRoute = L.map("route-map").setView([origin.lat, origin.lng], 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            const routeLayer = L.geoJSON(routeGeo, {
                style: { color: "blue", weight: 5 }
            }).addTo(mapRoute);

            mapRoute.fitBounds(routeLayer.getBounds());

            const distanceKm = (route.distance / 1000).toFixed(1);
            const totalMinutes = Math.round(route.duration / 60);
            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;

            const summaryDiv = document.getElementById("route-summary");
            if (summaryDiv) {
                document.getElementById("route-distance").textContent = distanceKm + " km";
                document.getElementById("route-duration").textContent = (hours > 0) ? `${hours} h ${minutes} min` : `${minutes} min`;
                summaryDiv.style.display = "block";
            }
            setTimeout(() => mapRoute.invalidateSize(), 200);
        } catch (e) {
            console.error("Error en Mapa de Ruta:", e);
        }
    }

    // --- MAPA 2: MONITOREO EN VIVO ---
    async function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;

        try {
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
            setInterval(update, 30000);
        } catch (e) { console.error("Error Mapa Vivo:", e); }
    }
})();
