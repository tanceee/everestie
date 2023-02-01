odoo.define('fiscalization.TransporterInfoPopup', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { posbus } = require('point_of_sale.utils')
    const { ConnectionLostError } = require('@web/core/network/rpc_service')

    /**
     * This popup needs to be self-dependent because it needs to be called from different place. In order to avoid code
     * Props:
     *  {
     *      product: a product object
     *      quantity: number
     *  }
     */
    class TransporterInfoPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = {
                all_clients: null,
            };
        }

        /*
         * Since this popup need to be self dependent, in case of an error, the popup need to be closed on its own.
         */
        mounted() {
            const order = this.env.pos.get_order()
            if (order && order.transporter) {
                var transporter = order.transporter
                var license = order.license
                var delivery_datetime = order.delivery_datetime
                if (transporter && license && delivery_datetime) {
                    $(this.el).find("#transporter").val(transporter)
                    $(this.el).find("#plate_number").val(license)
                    $(this.el).find("#delivery_datetime").val(delivery_datetime)
                }

            }
            else {
                var now = new Date()
                now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                var date_str = now.toISOString().slice(0, -1)
                const lastIndex = date_str.lastIndexOf(':');
                const before = date_str.slice(0, lastIndex);
                $(this.el).find("#delivery_datetime").val(before)
            }
        }

        setTransporter() {
            var transporter = $(this.el).find("#transporter").val()
            var license = $(this.el).find("#plate_number").val()
            var delivery_datetime = $(this.el).find("#delivery_datetime").val()
            const order = this.env.pos.get_order()
            if (order && transporter && license && delivery_datetime) {
                order.transporter = parseInt(transporter)
                order.license = license
                order.delivery_datetime = delivery_datetime
                order.save_to_db();
                this.cancel()
            }
            else {
                alert("Set value in the provided fields!")
            }
        }

        clearTransporter() {
            const pos_order = this.env.pos.get_order()
            pos_order.transporter = ""
            pos_order.license = ""
            pos_order.delivery_datetime = false
            pos_order.save_to_db();
            this.cancel()
        }

        getLicensePlate(event) {
            if ($(event.target).val()) {
                var license = $(event.target).find(':selected').data("license")
                if (license) {
                    $("#plate_number").val(license)
                }
            }
        }
    }

    TransporterInfoPopup.template = 'TransporterInfoPopup';
    Registries.Component.add(TransporterInfoPopup);
});
