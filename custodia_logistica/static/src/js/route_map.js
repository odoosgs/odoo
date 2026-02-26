(function () {
    "use strict";

    console.log("Custodia Logística: Scripts de mapa y acciones listos.");

    document.addEventListener("DOMContentLoaded", function () {
        setTimeout(() => {
            initPlannedRoute();
        }, 300);
    });

    // ==========================================
    // ESCUCHADOR DE CLICS CON CONFIRMACIÓN
    // ==========================================
    document.addEventListener("click", async function (e) {
        // Botón: Marcar llegada
        if (e.target.matches("#btn-llegada")) {
            const serviceId = e.target.dataset.serviceId;
            if (confirm("¿Confirmar llegada del custodio al punto de origen?")) {
                await executeCustodiaAction(serviceId, 'llegada');
            }
        }

        // Botón: Iniciar servicio
        if (e.target.matches("#btn-iniciar-servicio")) {
            const serviceId = e.target.dataset.serviceId;
            if (confirm("¿Desea iniciar formalmente la ejecución del servicio?")) {
                await executeCustodiaAction(serviceId, 'iniciar');
            }
        }
    });

    // Dentro del escuchador de clics en document.addEventListener("click"...)
    if (e.target.matches("#btn-incidencia")) {
        const serviceId = e.target.dataset.serviceId;
        const msg = document.getElementById("incidencia_msg").value;

        if (!msg) {
            alert("Por favor, describa la incidencia antes de enviar.");
            return;
        }

        if (confirm("¿Desea enviar este reporte de incidencia al centro de monitoreo?")) {
            try {
                const response = await fetch(`/custodia/service/${serviceId}/incidencia`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ params: { mensaje: msg } })
                });
                const data = await response.json();
                if (data.result && data.result.status === 'success') {
                    alert("Incidencia reportada correctamente.");
                    document.getElementById("incidencia_msg").value = ""; // Limpiar campo
                }
            } catch (err) {
                console.error("Error al enviar incidencia:", err);
            }
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
                // Efecto visual antes de recargar
                const btn = document.querySelector(action === 'llegada' ? "#btn-llegada" : "#btn-iniciar-servicio");
                if (btn) {
                    btn.innerHTML = '<i class="fa fa-check"></i> Registrando...';
                    btn.classList.replace('btn-warning', 'btn-success');
                }
                setTimeout(() => window.location.reload(), 800);
            } else {
                alert("Error: " + (data.result ? data.result.message : "No se pudo conectar con el servidor."));
            }
        } catch (err) {
            console.error("Error de red:", err);
            alert("Error de conexión. Verifica que el servidor de Odoo esté respondiendo.");
        }
    }

    // ... (Mantén tu función initPlannedRoute igual que antes) ...
    async function initPlannedRoute() {
        const container = document.getElementById("route-map");
        if (!container || !container.dataset.rutaId) return;
        const rutaId = container.dataset.rutaId;
        try {
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });
            const data = await response.json();
            if (!data.result || data.result.length === 0) return;
            const points = data.result;
            const map = L.map("route-map").setView([points[0].lat, points[0].lng], 10);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
            points.forEach(p => {
                let color = p.type === "origin" ? "green" : (p.type === "destination" ? "red" : "blue");
                L.circleMarker([p.lat, p.lng], { color: color, radius: 5 }).addTo(map);
            });
            const coords = points.map(p => p.lng + "," + p.lat).join(";");
            const osrmRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
            const osrmData = await osrmRes.json();
            if (osrmData.routes && osrmData.routes.length > 0) {
                const routeLine = L.geoJSON(osrmData.routes[0].geometry, { style: { color: "#003366", weight: 5 } }).addTo(map);
                map.fitBounds(routeLine.getBounds());
            }
        } catch (e) { console.error("Error mapa:", e); }
    }
})();
