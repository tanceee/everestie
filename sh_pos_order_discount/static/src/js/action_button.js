odoo.define("sh_pos_order_discount.action_button", function (require) {
    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class GlobalDiscountButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-global-discount-button", this.onClickGlobalDiscountButton);
        }
        onClickGlobalDiscountButton() {
            if (this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                this.env.pos.is_global_discount = true;
                let { confirmed, payload } = this.showPopup("GlobalDiscountPopupWidget");
                if (confirmed) {
                } else {
                    return;
                }
            } else {
                alert("Add Product In Cart.");
            }
        }
    }
    GlobalDiscountButton.template = "GlobalDiscountButton";
    ProductScreen.addControlButton({
        component: GlobalDiscountButton,
        condition: function () {
            return this.env.pos.config.sh_allow_global_discount;
        },
    });
    Registries.Component.add(GlobalDiscountButton);

    class RemoveDiscountButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-remove-discount-button", this.onClickRemoveDiscountButton);
        }
        onClickRemoveDiscountButton() {
            var orderlines = this.env.pos.get_order().get_orderlines();
            if (orderlines) {
                _.each(orderlines, function (each_orderline) {
                    each_orderline.set_discount(0);
                    each_orderline.set_global_discount(0);
                });
            }
        }
    }
    RemoveDiscountButton.template = "RemoveDiscountButton";
    ProductScreen.addControlButton({
        component: RemoveDiscountButton,
        condition: function () {
            return this.env.pos.config.sh_allow_global_discount || this.env.pos.config.sh_allow_order_line_discount;
        },
    });
    Registries.Component.add(RemoveDiscountButton);

    return { GlobalDiscountButton, RemoveDiscountButton };
});
