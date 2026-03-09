(function () {
    "use strict";

    console.log("Archivo route_map.js cargado exitosamente.");

    // =========================================================
    // 1. LÓGICA DE FILTRADO DE SELECTORES (DELEGACIÓN)
    // Se registra de inmediato para que funcione en cualquier momento
    // =========================================================
    document.addEventListener("change", async function (e) {
        if (e.target && e.target.id === "ruta_maestra_id") {
            const maestraId = e.target.value;
            const origenSelect = document.getElementById("nodo_origen_id");
            const destinoSelect = document.getElementById("nodo_destino_id");

            console.log("Cambio en Ruta Maestra detectado. ID:", maestraId);

            if (!maestraId || !origenSelect || !destinoSelect) return;

            try {
                // Fetch estándar compatible con type='http'
                const response = await fetch(`/get_nodos_by_maestra/${maestraId}`);
                if (!response.ok) return;

                const result = await response.json();

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

                // Desbloqueo físico de campos
                origenSelect.disabled = false;
                destinoSelect.disabled = false;
                origenSelect.removeAttribute('disabled');
                destinoSelect.removeAttribute('disabled');
                
                console.log("Selectores de nodos actualizados y habilitados.");

            } catch (err) {
                console.error("Error en el filtrado de nodos:", err);
            }
        }
    });

    // =========================================================
    // 2. ARRANCAR MAPAS AL CARGAR LA PÁGINA (DOMContentReady)
    // =========================================================
    document.addEventListener("DOMContentLoaded", function () {
        console.log("DOM listo - Verificando existencia de mapas...");

        // Pequeño retraso para asegurar que los elementos del portal estén renderizados
        setTimeout(() => {
            const routeMapContainer = document.getElementById("route-map");
            const liveMapContainer = document.getElementById("live-map");

            if (routeMapContainer) {
                console.log("Iniciando Mapa de Ruta Planeada...");
                initPlannedRouteMap();
            }

            if (liveMapContainer) {
                console.log("Iniciando Mapa de Monitoreo en Vivo...");
                initLiveTrackingMap();
            }
        }, 500);
    });

    // =========================================================
    // 3. FUNCIÓN: MAPA 1 - RUTA PLANEADA
    // =========================================================
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
            console.error("Error al inicializar Mapa de Ruta:", e);
        }
    }

    // =========================================================
    // 4. FUNCIÓN: MAPA 2 - MONITOREO EN VIVO
    // =========================================================
    async function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;

        try {
            // Inicializamos el mapa con una vista general de México
            const mapLive = L.map("live-map").setView([23.6345, -102.5528], 5);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
            const marker = L.marker([23.6345, -102.5528]).addTo(mapLive);

            async function update() {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos).bindPopup("Última actualización: " + data.last_update).openPopup();
                    mapLive.panTo(pos);
                    // Si el zoom es el inicial muy lejano, acercamos
                    if (mapLive.getZoom() < 10) mapLive.setZoom(13);
                }
            }

            setTimeout(() => { 
                mapLive.invalidateSize(); 
                update(); 
            }, 200);

            setInterval(update, 30000);
        } catch (e) { 
            console.error("Error al inicializar Mapa en Vivo:", e); 
        }
    }
})();
