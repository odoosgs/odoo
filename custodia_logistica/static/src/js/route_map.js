(function () {
    "use strict";

    // Función de ayuda para mostrar mensajes en el mapa
    function setMapMessage(containerId, message) {
        const el = document.getElementById(containerId);
        if (el) el.innerHTML = `<div class="d-flex align-items-center justify-content-center h-100 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div> ${message}</div>`;
    }

    document.addEventListener("DOMContentLoaded", function () {
        // Verificamos si Leaflet (L) ya cargó, si no, esperamos un momento
        const checkLeaflet = setInterval(() => {
            if (typeof L !== 'undefined') {
                clearInterval(checkLeaflet);
                console.log("Custodia Logística: Leaflet listo, iniciando mapas...");
                initMaps();
            }
        }, 100);
    });

    async function initMaps() {
        const routeContainer = document.getElementById("route-map");
        if (routeContainer && routeContainer.dataset.rutaId) {
            setMapMessage("route-map", "Cargando ruta planeada...");
            await drawPlannedRoute(routeContainer.dataset.rutaId);
        }

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

            if (!coords || coords.length < 2) {
                document.getElementById("route-map").innerHTML = "Error: Coordenadas no encontradas.";
                return;
            }

            // Limpiamos el mensaje de "Cargando" antes de iniciar el mapa
            document.getElementById("route-map").innerHTML = "";

            const origin = [coords[0].lat, coords[0].lng];
            const mapRoute = L.map("route-map").setView(origin, 6);
            
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap"
            }).addTo(mapRoute);

            // Marcadores inmediatos
            L.marker(origin).addTo(mapRoute).bindPopup("Origen");
            L.marker([coords[coords.length-1].lat, coords[coords.length-1].lng]).addTo(mapRoute).bindPopup("Destino");

            // OSRM para carretera real
            const osrmCoords = coords.map(p => p.lng + "," + p.lat).join(";");
            fetch(`https://router.project-osrm.org/route/v1/driving/${osrmCoords}?overview=full&geometries=geojson`)
                .then(res => res.json())
                .then(osrmData => {
                    if (osrmData.routes && osrmData.routes.length > 0) {
                        const routeGeo = L.geoJSON(osrmData.routes[0].geometry, {
                            style: { color: "blue", weight: 5, opacity: 0.8 }
                        }).addTo(mapRoute);
                        mapRoute.fitBounds(routeGeo.getBounds());
                    }
                });

            setTimeout(() => mapRoute.invalidateSize(), 500);
        } catch (e) { 
            console.error("Error:", e);
            document.getElementById("route-map").innerHTML = "Error al conectar con el servidor de mapas.";
        }
    }

    // ... aquí sigue tu función de initLiveTracking y clics ...
})();
