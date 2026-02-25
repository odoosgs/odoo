(function () {
    "use strict";

    console.log("Custodia Logística: Inicializando scripts de mapa...");

    document.addEventListener("DOMContentLoaded", function () {
        // Pequeño retraso para asegurar que Leaflet (L) esté cargado
        setTimeout(() => {
            initPlannedRoute();
        }, 300);
    });

    async function initPlannedRoute() {
        const container = document.getElementById("route-map");
        if (!container || !container.dataset.rutaId) return;

        const rutaId = container.dataset.rutaId;
        console.log("Cargando ruta ID:", rutaId);

        try {
            // Usamos fetch nativo para no depender de librerías de Odoo
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });
            const data = await response.json();

            if (!data.result || data.result.length === 0) {
                console.warn("No se recibieron coordenadas.");
                return;
            }

            const points = data.result;
            // Inicializar el mapa de Leaflet
            const map = L.map("route-map").setView([points[0].lat, points[0].lng], 10);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap"
            }).addTo(map);

            // Dibujar puntos
            points.forEach(p => {
                let color = p.type === "origin" ? "green" : (p.type === "destination" ? "red" : "blue");
                L.circleMarker([p.lat, p.lng], { color: color, radius: 5 }).addTo(map);
            });

            // Trazado de carretera vía OSRM
            const coords = points.map(p => p.lng + "," + p.lat).join(";");
            const osrmRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
            const osrmData = await osrmRes.json();

            if (osrmData.routes && osrmData.routes.length > 0) {
                const routeLine = L.geoJSON(osrmData.routes[0].geometry, {
                    style: { color: "#003366", weight: 5 }
                }).addTo(map);
                map.fitBounds(routeLine.getBounds());
            }
        } catch (e) {
            console.error("Error en initPlannedRoute:", e);
        }
    }

(function () {
    "use strict";

    console.log("Custodia Logística: Inicializando scripts de mapa y acciones...");

    document.addEventListener("DOMContentLoaded", function () {
        // Pequeño retraso para asegurar que Leaflet (L) esté cargado
        setTimeout(() => {
            initPlannedRoute();
        }, 300);
    });

    // ==========================================
    // ESCUCHADOR DE CLICS (Para la demostración)
    // ==========================================
    document.addEventListener("click", async function (e) {
        // Botón: Marcar llegada
        if (e.target.matches("#btn-llegada")) {
            const serviceId = e.target.dataset.serviceId;
            await executeCustodiaAction(serviceId, 'llegada');
        }

        // Botón: Iniciar servicio
        if (e.target.matches("#btn-iniciar-servicio")) {
            const serviceId = e.target.dataset.serviceId;
            await executeCustodiaAction(serviceId, 'iniciar');
        }
    });

    // Función auxiliar para enviar datos a Odoo
    async function executeCustodiaAction(serviceId, action) {
        console.log(`Ejecutando acción: ${action} para el servicio: ${serviceId}`);
        try {
            const response = await fetch(`/custodia/service/${serviceId}/${action}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} }) 
            });
            const data = await response.json();
            
            if (data.result && data.result.status === 'success') {
                window.location.reload(); // Refresca para ver los nuevos tiempos calculados
            } else {
                console.error("Error en la respuesta de Odoo:", data);
                alert("No se pudo completar la acción. Revisa la consola.");
            }
        } catch (err) {
            console.error("Error de conexión:", err);
        }
    }

    // ==========================================
    // RUTA PLANEADA (Mapa)
    // ==========================================
    async function initPlannedRoute() {
        const container = document.getElementById("route-map");
        if (!container || !container.dataset.rutaId) return;

        const rutaId = container.dataset.rutaId;
        console.log("Cargando mapa para ruta ID:", rutaId);

        try {
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });
            const data = await response.json();

            if (!data.result || data.result.length === 0) {
                console.warn("No se recibieron coordenadas de la ruta.");
                return;
            }

            const points = data.result;
            const map = L.map("route-map").setView([points[0].lat, points[0].lng], 10);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap"
            }).addTo(map);

            points.forEach(p => {
                let color = p.type === "origin" ? "green" : (p.type === "destination" ? "red" : "blue");
                L.circleMarker([p.lat, p.lng], { color: color, radius: 5 }).addTo(map);
            });

            const coords = points.map(p => p.lng + "," + p.lat).join(";");
            const osrmRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
            const osrmData = await osrmRes.json();

            if (osrmData.routes && osrmData.routes.length > 0) {
                const routeLine = L.geoJSON(osrmData.routes[0].geometry, {
                    style: { color: "#003366", weight: 5 }
                }).addTo(map);
                map.fitBounds(routeLine.getBounds());
            }
        } catch (e) {
            console.error("Error en initPlannedRoute:", e);
        }
    }
})();    
})();
