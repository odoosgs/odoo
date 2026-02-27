(function () {
    "use strict";

    console.log("Custodia Logística: Iniciando scripts...");

    document.addEventListener("DOMContentLoaded", function () {
        // Ejecutamos el mapa después de un breve delay para asegurar que el DOM esté listo
        setTimeout(() => {
            initPlannedRoute();
        }, 500);
    });

    // UNIFICAMOS TODOS LOS CLICS AQUÍ
    document.addEventListener("click", async function (e) {
        
        // 1. Lógica para Marcar Llegada
        if (e.target.matches("#btn-llegada")) {
            const serviceId = e.target.dataset.serviceId;
            if (confirm("¿Confirmar llegada del custodio?")) {
                await executeCustodiaAction(serviceId, 'llegada');
            }
        }

        // 2. Lógica para Iniciar Servicio
        if (e.target.matches("#btn-iniciar-servicio")) {
            const serviceId = e.target.dataset.serviceId;
            if (confirm("¿Desea iniciar la ejecución del servicio?")) {
                await executeCustodiaAction(serviceId, 'iniciar');
            }
        }

        // 3. Lógica para Enviar Incidencia (CORREGIDA: Ahora dentro del evento 'e')
        if (e.target.matches("#btn-incidencia")) {
            const serviceId = e.target.dataset.serviceId;
            const msgInput = document.getElementById("incidencia_msg");
            const msg = msgInput ? msgInput.value : "";
            
            if (!msg) {
                alert("Por favor, describa la incidencia.");
                return;
            }

            if (confirm("¿Enviar reporte de incidencia?")) {
                try {
                    const response = await fetch(`/custodia/service/${serviceId}/incidencia`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ params: { mensaje: msg } })
                    });
                    const data = await response.json();
                    if (data.result && data.result.status === 'success') {
                        alert("Reporte enviado al Chatter.");
                        msgInput.value = ""; 
                    }
                } catch (err) {
                    console.error("Error al enviar incidencia:", err);
                }
            }
        }
    });

    // Función para el Mapa (La que dibuja la ruta azul de tu foto)
    async function initPlannedRoute() {
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
            if (!data.result || data.result.length === 0) return;

            const points = data.result;
            // Inicializamos el mapa
            const map = L.map("route-map").setView([points[0].lat, points[0].lng], 7);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

            // Marcadores de Inicio y Destino
            points.forEach(p => {
                let color = p.type === "origin" ? "green" : (p.type === "destination" ? "red" : "blue");
                L.circleMarker([p.lat, p.lng], { color: color, radius: 6 }).addTo(map);
            });

            // Trazado de Carretera OSRM
            const coords = points.map(p => p.lng + "," + p.lat).join(";");
            const osrmRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
            const osrmData = await osrmRes.json();
            
            if (osrmData.routes && osrmData.routes.length > 0) {
                const routeLine = L.geoJSON(osrmData.routes[0].geometry, { 
                    style: { color: "blue", weight: 6 } // Color azul como en tu imagen
                }).addTo(map);
                map.fitBounds(routeLine.getBounds());
            }
        } catch (e) {
            console.error("Error cargando el mapa:", e);
        }
    }

    async function executeCustodiaAction(serviceId, action) {
        try {
            const response = await fetch(`/custodia/service/${serviceId}/${action}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} }) 
            });
            const data = await response.json();
            if (data.result && data.result.status === 'success') {
                window.location.reload();
            }
        } catch (err) {
            console.error("Error en acción:", err);
        }
    }
})();
