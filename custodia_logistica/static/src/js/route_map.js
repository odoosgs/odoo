/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {

    const mapContainer = document.getElementById("route_map");
    if (!mapContainer) {
        return;
    }

    const serviceId = mapContainer.dataset.serviceId;
    const accessToken = mapContainer.dataset.token;

    if (!serviceId || !accessToken) {
        console.warn("Faltan datos para inicializar el mapa");
        return;
    }

    // Inicializar mapa
    const map = L.map("route_map").setView([19.4326, -99.1332], 6);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    let marker = null;

    async function loadTracking() {
        try {
            const response = await fetch(
                `/mis-servicios/${serviceId}/tracking?access_token=${accessToken}`,
                {
                    method: "GET",
                }
            );

            if (!response.ok) {
                console.error("Error HTTP:", response.status);
                return;
            }

            const data = await response.json();

            if (data.error) {
                console.error("Error:", data.error);
                return;
            }

            if (!data.lat || !data.lng) {
                console.warn("Sin coordenadas aún");
                return;
            }

            const latLng = [parseFloat(data.lat), parseFloat(data.lng)];

            if (!marker) {
                marker = L.marker(latLng).addTo(map);
                map.setView(latLng, 14);
            } else {
                marker.setLatLng(latLng);
            }

        } catch (error) {
            console.error("Error cargando tracking:", error);
        }
    }

    // Cargar primera vez
    loadTracking();

    // Actualizar cada 10 segundos
    setInterval(loadTracking, 10000);
});
