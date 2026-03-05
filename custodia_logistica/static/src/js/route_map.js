(function () {
    "use strict";

    console.log("Archivo route_map.js detectado por el navegador");

    document.addEventListener("DOMContentLoaded", function () {
        console.log("DOM completamente cargado - Iniciando lógica de Custodia");

        // 1. Inicializar mapas si existen los contenedores
        setTimeout(() => { 
            if (document.getElementById("route-map")) initPlannedRouteMap(); 
        }, 200);
        
        setTimeout(() => { 
            if (document.getElementById("live-map")) initLiveTrackingMap(); 
        }, 600);

        // 2. Lógica de Filtrado en Cascada (Selectores del Formulario)
        const maestroSelect = document.getElementById("ruta_maestra_id");
        const origenSelect = document.getElementById("nodo_origen_id");
        const destinoSelect = document.getElementById("nodo_destino_id");

        if (maestroSelect) {
            console.log("Selector de Ruta Maestra encontrado");

            maestroSelect.addEventListener("change", async function() {
                const maestraId = this.value;
                console.log("Cambio detectado en Ruta Maestra. ID seleccionado:", maestraId);

                if (!maestraId) {
                    origenSelect.disabled = true;
                    destinoSelect.disabled = true;
                    origenSelect.innerHTML = '<option value="">Primero seleccione ruta...</option>';
                    return;
                }

                try {
                    console.log("Enviando petición fetch a Odoo...");
                    const response = await fetch(`/get_nodos_by_maestra/${maestraId}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ params: {} }) 
                    });

                    const data = await response.json();
                    console.log("Respuesta recibida de Odoo:", data);

                    if (data.result) {
                        const result = data.result;

                        // Llenar Origen
                        origenSelect.innerHTML = '<option value="">Seleccione salida...</option>';
                        result.origenes.forEach(n => {
                            let opt = document.createElement('option');
                            opt.value = n.id;
                            opt.textContent = n.name;
                            origenSelect.appendChild(opt);
                        });

                        // Llenar Destino
                        destinoSelect.innerHTML = '<option value="">Seleccione llegada...</option>';
                        result.destinos.forEach(n => {
                            let opt = document.createElement('option');
                            opt.value = n.id;
                            opt.textContent = n.name;
                            destinoSelect.appendChild(opt);
                        });
                        
                        origenSelect.disabled = false;
                        destinoSelect.disabled = false;
                        console.log("Selectores de origen y destino actualizados");
                    }
                } catch (e) {
                    console.error("Error en el proceso de filtrado:", e);
                }
            });
        }
    });

    // --- FUNCIONES DE MAPAS (Mantener las que ya tenías) ---
    async function initPlannedRouteMap() { /* ... tu código anterior del mapa planeado ... */ }
    async function initLiveTrackingMap() { /* ... tu código anterior del mapa en vivo ... */ }

})();
