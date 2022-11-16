odoo.define("sh_pos_order_discount.screen", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const NumpadWidget = require("point_of_sale.NumpadWidget");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const OrderWidget = require("point_of_sale.OrderWidget");

    const PosNumpadWidget = (NumpadWidget) =>
        class extends NumpadWidget {
            changeMode(mode) {
                super.changeMode(mode);
                var self = this;
                if (mode && mode == "discount" && self.env.pos.config.sh_allow_order_line_discount) {
                    self.env.pos.is_global_discount = false;
                    let { confirmed, payload } = this.showPopup("GlobalDiscountPopupWidget");
                    if (confirmed) {
                    } else {
                        return;
                    }
                }
            }
        };
    Registries.Component.extend(NumpadWidget, PosNumpadWidget);

    const ShProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            _setValue(val) {
                super._setValue(val);

                var mode = this.state.numpadMode;
                var order = this.env.pos.get_order();
                if (order.get_selected_orderline()) {
                    if (mode == "discount") {
                        order.get_selected_orderline().set_discount(0);
                        order.get_selected_orderline().set_discount(order.get_selected_orderline().get_global_discount());

                        var price = order.get_selected_orderline().get_display_price();
                        var current_price = (price * val) / 100;
                        var discount = ((order.get_selected_orderline().price * order.get_selected_orderline().quantity - current_price) / (order.get_selected_orderline().price * order.get_selected_orderline().quantity)) * 100;
                        order.get_selected_orderline().set_discount(discount);
                    }
                }
            }
            
        };
    Registries.Component.extend(ProductScreen, ShProductScreen);
    
    const ShOrderWidget = (OrderWidget) =>
    class extends OrderWidget {
        constructor() {
            super(...arguments);
        }
        _updateSummary() {
            $('.summary').addClass('sh_summary')
            super._updateSummary();
            var order = this.env.pos.get_order();
            var total_discount = 0;
            if (this.env.pos.get_order().get_orderlines()) {
                _.each(this.env.pos.get_order().get_orderlines(), function (each_orderline) {
                    total_discount = total_discount + (each_orderline.price * each_orderline.quantity - each_orderline.get_display_price());
                });
            }
            
            $('span.subentry').text('Amount: '+ total_discount.toFixed(2) );
            
        }
    }
    Registries.Component.extend(OrderWidget, ShOrderWidget);
});
