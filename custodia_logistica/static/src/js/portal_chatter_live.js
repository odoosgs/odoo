/** @odoo-module **/

import { publicWidget } from "@web/legacy/js/public/public_widget";

publicWidget.registry.CustodiaChatterLive = publicWidget.Widget.extend({
    selector: '#service_chatter',

    /**
     * @override
     */
    start: function () {
        this.resId = parseInt(this.$el.attr('data-res-id'));
        this.resModel = this.$el.attr('data-res-model');
        
        if (this.resId && this.resModel === 'custodia.service') {
            // Verificamos que el servicio de bus esté disponible antes de llamar
            if (this.call) {
                this.call('bus_service', 'addChannel', `custodia_service_${this.resId}`);
                this.call('bus_service', 'subscribe', `custodia_service_${this.resId}`, this._onNotification.bind(this));
            }
        }
        return this._super.apply(this, arguments);
    },

    /**
     * Manejador de notificaciones del bus
     */
    _onNotification: function (payload) {
        if (payload && payload.type === 'mail.record/insert' && payload.res_id === this.resId) {
            // No refrescar si el usuario tiene el foco en el editor para evitar que se le borre lo que escribe
            const $composer = this.$('.o_portal_chatter_composer_body');
            if ($composer.length === 0 || !$composer.is(':focus')) {
                this._refreshChatter();
            }
        }
    },

    /**
     * Recarga parcial del contenedor de mensajes
     */
    _refreshChatter: function() {
        const $messages = this.$('.o_portal_chatter_messages');
        if ($messages.length) {
            // Refresca solo la sección de mensajes usando el endpoint actual
            $messages.load(window.location.href + " .o_portal_chatter_messages > *");
        }
    }
});
