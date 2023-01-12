odoo.define('fiscalization.TransporterInfoButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class TransporterInfoButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }

        onClick() {
            const orderline = this.env.pos.get_order().get_orderlines()
            const order = this.env.pos.get_order()
            if (orderline.length) {
                const all_customers = this.customers()
                this.showPopup('TransporterInfoPopup', { order, all_customers });
            }
            else {
                alert("Add Some Product to the order!")
            }
        }

        customers() {
            let res;
            res = this.env.pos.db.get_partners_sorted();
            var transporter = []
            res.forEach(partner => {
                if (partner.is_transporter) {
                    transporter.push(partner)
                }
            });
            return transporter.sort(function (a, b) { return (a.name || '').localeCompare(b.name || '') });
        }
    }

    TransporterInfoButton.template = 'TransporterInfoButton';

    ProductScreen.addControlButton({
        component: TransporterInfoButton,
        condition: function(){
          return this.env.pos.config.enable_transporter;
        },
        position: ['before', 'SetFiscalPositionButton'],
    });

    Registries.Component.add(TransporterInfoButton);

    return TransporterInfoButton;
});
