(function () {
    "use strict";

    console.log("Archivo route_map.js detectado por el navegador");

document.addEventListener("DOMContentLoaded", function () {
        console.log("Archivo route_map.js activo en el Portal");

        const maestroSelect = document.getElementById("ruta_maestra_id");
        const origenSelect = document.getElementById("nodo_origen_id");
        const destinoSelect = document.getElementById("nodo_destino_id");

        if (maestroSelect) {
            console.log("Formulario de solicitud detectado");

            // Forzamos el reset de los campos al cargar por si acaso
            origenSelect.disabled = true;
            destinoSelect.disabled = true;

            maestroSelect.addEventListener("change", async function(e) {
                const maestraId = e.target.value; // Usamos e.target para mayor precisión
                console.log("Evento change disparado. ID:", maestraId);

                if (!maestraId) {
                    origenSelect.disabled = true;
                    destinoSelect.disabled = true;
                    return;
                }

                try {
                    // Petición HTTP estándar (GET)
                    const response = await fetch(`/get_nodos_by_maestra/${maestraId}`);
                    
                    if (!response.ok) {
                        console.error("Error en respuesta del servidor:", response.status);
                        return;
                    }

                    const result = await response.json();
                    console.log("Nodos recibidos:", result);

                    // Limpiar y llenar Origen
                    origenSelect.innerHTML = '<option value="">-- Seleccione salida --</option>';
                    result.origenes.forEach(n => {
                        let opt = document.createElement('option');
                        opt.value = n.id;
                        opt.textContent = n.name;
                        origenSelect.appendChild(opt);
                    });

                    // Limpiar y llenar Destino
                    destinoSelect.innerHTML = '<option value="">-- Seleccione llegada --</option>';
                    result.destinos.forEach(n => {
                        let opt = document.createElement('option');
                        opt.value = n.id;
                        opt.textContent = n.name;
                        destinoSelect.appendChild(opt);
                    });

                    // HABILITAR LOS CAMPOS
                    origenSelect.disabled = false;
                    destinoSelect.disabled = false;
                    console.log("Campos de nodos habilitados");

                } catch (err) {
                    console.error("Error al procesar el filtrado:", err);
                }
            });
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
