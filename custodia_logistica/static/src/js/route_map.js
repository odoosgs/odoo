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
        
        // CORRECCIÓN: Extraemos el arreglo de resultados de Odoo
        const coords = data.result;

        if (!coords || coords.length < 2) {
            console.error("Coordenadas insuficientes para dibujar la ruta", coords);
            return;
        }

        // Definimos Origen y Destino basados en la posición en el Array
        const origin = [coords[0].lat, coords[0].lng];
        const dest   = [coords[coords.length - 1].lat, coords[coords.length - 1].lng];

        console.log("Iniciando mapa en:", origin);

        // Inicializar mapa centrado en el origen
        const map = L.map("route-map").setView(origin, 6);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap"
        }).addTo(map);

        // Añadir marcadores
        L.marker(origin).addTo(map).bindPopup("Origen");
        L.marker(dest).addTo(map).bindPopup("Destino");

        // Dibujar línea simple entre puntos (Polyline)
        const path = coords.map(p => [p.lat, p.lng]);
        L.polyline(path, { color: "blue", weight: 5 }).addTo(map);

        // Ajustar el zoom para que se vean todos los puntos
        map.fitBounds(L.polyline(path).getBounds());
        
        // Forzar renderizado por si el contenedor estaba oculto
        setTimeout(() => map.invalidateSize(), 400);

    } catch (e) {
        console.error("Error crítico en el mapa:", e);
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
