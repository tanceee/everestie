odoo.define('skip_pos_fiscalization', function (require) {
    'use strict';
    const models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const PaymentScreen = require('point_of_sale.PaymentScreen');


    models.load_fields("pos.order", ['skip_fiscalization']);
    var _super = models.Order;

    var _posmodel_super = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        initialize: function () {
            _posmodel_super.initialize.apply(this, arguments);
            this.ready.then(() => {
                this.disable_fiscalization = this.config.disable_fiscalization
            });
        },
    });

    models.Order = models.Order.extend({
        //@Override
        initialize: function (attributes, options) {
            _super.prototype.initialize.apply(this, arguments);

            if (options.json) {

            }
            else {
                this.skip_fiscalization = false
            }
        },

        init_from_JSON: function (json) {
            this.skip_fiscalization = json.skip_fiscalization
            _super.prototype.init_from_JSON.apply(this, arguments);

        },
        export_as_JSON: function () {
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            json.skip_fiscalization = this.skip_fiscalization
            return json
        },

        set_to_skip_fiscalization: function (skip_fiscalization) {
            this.assert_editable();
            this.skip_fiscalization = skip_fiscalization;
            if (skip_fiscalization && this.pos.config.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = true
            }
            else if (!skip_fiscalization && this.pos.config.disable_fiscalization == true && this.pos.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = false
            }
            else if (this.pos.config.disable_fiscalization == true && this.pos.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = false
            }
        },

        is_skip_fiscalization: function () {
            return this.skip_fiscalization;
        },
    });

    const PosPaymentScreenExt = (PaymentScreen) => class extends PaymentScreen {
        toggle_skip_fiscalization() {
            this.currentOrder.set_to_skip_fiscalization(!this.currentOrder.is_skip_fiscalization());
            this.render();
        }
    }

    const ProductScreenExt = ProductScreen => class extends ProductScreen {
        async _onClickPay() {
            var skip_fiscalization = this.currentOrder.is_skip_fiscalization()
            if (skip_fiscalization && this.env.pos.config.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = true
            }
            else if (!skip_fiscalization && this.env.pos.config.disable_fiscalization == true && this.env.pos.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = false
            }
            else if (this.env.pos.config.disable_fiscalization == true && this.env.pos.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = false
            }
            super._onClickPay()
        }
    }

    Registries.Component.extend(PaymentScreen, PosPaymentScreenExt);
    Registries.Component.extend(ProductScreen, ProductScreenExt);

});