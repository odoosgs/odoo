/** @odoo-module **/

import { publicWidget } from "@web/legacy/js/public/public_widget";
import { bus } from 'web.core';

publicWidget.registry.CustodiaChatterLive = publicWidget.Widget.extend({
    selector: '.o_portal_chatter', // Se cuelga del chatter estándar del portal
    
    start: function () {
        const self = this;
        // Obtenemos el ID del servicio y el modelo de los datos del DOM
        this.resId = parseInt($("span[data-res-id]").data('res-id'));
        this.resModel = 'custodia.service';

        if (this.resId) {
            // Nos suscribimos al canal de notificaciones de este registro específico
            this.call('bus_service', 'addChannel', `custodia_service_${this.resId}`);
            this.call('bus_service', 'onNotification', this, this._onNotification);
        }
        return this._super.apply(this, arguments);
    },

    _onNotification: function (notifications) {
        const self = this;
        notifications.forEach(notif => {
            // Si llega una notificación de tipo 'message_post' para este servicio
            if (notif.type === 'mail.record/insert' && notif.payload.res_id === self.resId) {
                // Refrescamos solo el widget del chatter sin recargar toda la web
                self._refreshChatter();
            }
        });
    },

    _refreshChatter: function() {
        // Ejecuta la recarga parcial del contenedor de mensajes
        $(".o_portal_chatter_messages").load(window.location.href + " .o_portal_chatter_messages > *");
        console.log("Chatter actualizado en tiempo real para el folio de custodia.");
    }
});
