odoo.define("sh_pos_default_invoice.pos", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const PaymentScreen = require("point_of_sale.PaymentScreen");

    const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
                if (this.env.pos.config.sh_enable_default_invoice) {
                    this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                    this.render();
                }
            }
        };
    Registries.Component.extend(PaymentScreen, PosResPaymentScreen);
});
