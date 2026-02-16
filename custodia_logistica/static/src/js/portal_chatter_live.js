/** @odoo-module **/

import { publicWidget } from "@web/legacy/js/public/public_widget";

publicWidget.registry.CustodiaChatterLive = publicWidget.Widget.extend({
    selector: '.o_portal_chatter_container', // Selector nativo más seguro
    
    start: function () {
        this.resId = parseInt(this.$el.attr('data-res-id'));
        if (this.resId && this.call) {
            this.call('bus_service', 'addChannel', `custodia_service_${this.resId}`);
            this.call('bus_service', 'subscribe', `custodia_service_${this.resId}`, this._onNotification.bind(this));
        }
        return this._super.apply(this, arguments);
    },

    _onNotification: function (payload) {
        // Verificamos que el payload tenga la estructura esperada
        if (payload && payload.type === 'mail.record/insert' && payload.res_id === this.resId) {
            const $composer = this.$('.o_portal_chatter_composer_body');
            if ($composer.length && !$composer.is(':focus')) {
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
