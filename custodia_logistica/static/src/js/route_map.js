/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";

document.addEventListener("DOMContentLoaded", function () {
    // Esperamos un momento a que el DOM esté listo para Leaflet
    setTimeout(() => {
        initPlannedRoute();
        initLiveTracking();
        initCustodioActions();
    }, 500);
});

async function initPlannedRoute() {
    const routeContainer = document.getElementById("route-map");
    if (!routeContainer || !routeContainer.dataset.rutaId) return;

    const rutaId = routeContainer.dataset.rutaId;

    try {
        // Nueva forma de llamar a controladores JSON en Odoo moderno
        const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ params: {} })
        });
        const data = await response.json();

        if (!data.result || !data.result.length) {
            console.warn("No hay coordenadas para la ruta.");
            return;
        }

        const points = data.result;
        const firstPoint = points[0];

        // Inicializar mapa
        const routeMap = L.map("route-map").setView([firstPoint.lat, firstPoint.lng], 6);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap"
        }).addTo(routeMap);

        // Dibujar Marcadores
        points.forEach(p => {
            let color = "blue";
            if (p.type === "origin") color = "green";
            if (p.type === "destination") color = "red";

            L.circleMarker([p.lat, p.lng], {
                radius: 6,
                color: color,
                fillColor: color,
                fillOpacity: 1
            }).addTo(routeMap);
        });

        // Llamada a OSRM
        const coords = points.map(p => p.lng + "," + p.lat).join(";");
        const osrmRes = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
        const osrmData = await osrmRes.json();

        if (osrmData.routes && osrmData.routes.length) {
            const routeData = osrmData.routes[0];
            const geojsonLayer = L.geoJSON(routeData.geometry, {
                style: { color: "#003366", weight: 5 }
            }).addTo(routeMap);

            routeMap.fitBounds(geojsonLayer.getBounds());
            
            // Actualizar resumen (distancia/tiempo)
            const summary = document.getElementById("route-summary");
            if (summary) {
                const distanceKm = (routeData.distance / 1000).toFixed(2);
                const durationHrs = Math.floor(routeData.duration / 3600);
                const durationMin = Math.round((routeData.duration % 3600) / 60);
                
                document.getElementById("route-distance").innerText = distanceKm + " km";
                document.getElementById("route-duration").innerText = `${durationHrs}h ${durationMin}min`;
                summary.style.display = "block";
            }
        }
    } catch (error) {
        console.error("Error en el mapa:", error);
    }
}

// Las funciones initLiveTracking y initCustodioActions 
// deben seguir un patrón similar (async/await y sin require).
