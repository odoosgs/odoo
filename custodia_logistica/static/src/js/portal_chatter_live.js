/** @odoo-module **/

import { publicWidget } from "@web/legacy/js/public/public_widget";

publicWidget.registry.CustodiaChatterLive = publicWidget.Widget.extend({
    selector: '#service_chatter', // Usamos el ID que pusimos en el XML
    
    start: function () {
        this.resId = parseInt(this.$el.data('res-id'));
        if (this.resId) {
            // Usamos el servicio de bus de Odoo de forma segura
            this.call('bus_service', 'addChannel', `custodia_service_${this.resId}`);
            this.call('bus_service', 'subscribe', `custodia_service_${this.resId}`, this._onNotification.bind(this));
        }
        return this._super.apply(this, arguments);
    },

    _onNotification: function (payload) {
        if (payload.type === 'mail.record/insert' && payload.res_id === this.resId) {
            // Solo refrescamos si el usuario no está escribiendo
            if (!this.$('.o_portal_chatter_composer_body').is(':focus')) {
                this._refreshChatter();
            }
        }
    },

    _refreshChatter: function() {
        const $messages = this.$('.o_portal_chatter_messages');
        if ($messages.length) {
            $messages.load(window.location.href + " .o_portal_chatter_messages > *");
        }
    }
});
