odoo.define("sh_pos_order_discount.popup", function (require) {
    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class GlobalDiscountPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        mounted(){
            super.mounted()
            $(".sh_discount_value").focus()
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });

            if (!$(".sh_discount_value").val()) {
                alert("Enter amount of discount.");
                $(".sh_discount_value").addClass("invalid_number");
            } else if (
                ($(".sh_discount_value").val() && parseFloat($(".sh_discount_value").val()) > 100 && document.getElementById("discount_percentage_radio") && document.getElementById("discount_percentage_radio").checked) ||
                ($(".sh_discount_value").val() && parseFloat($(".sh_discount_value").val()) < 0) ||
                !/^\d*\.?\d*$/.test(parseFloat($(".sh_discount_value").val()))
            ) {
                $(".sh_discount_value").addClass("invalid_number");
                $(".sh_discount_value").val(" ");
                $(".sh_discount_value").focus();
            } else {
                var value = $(".sh_discount_value").val();
                if (document.getElementById("discount_fixed_radio") && document.getElementById("discount_fixed_radio").checked) {
                    if (self.env.pos.is_global_discount) {
                        var order_total = self.env.pos.get_order().get_total_with_tax();
                        var orderlines = self.env.pos.get_order().get_orderlines();
                        var temp = value / orderlines.length;
                        var final_total = self.env.pos.get_order().get_total_with_tax() - value;
                        temp = parseInt(temp);
                        if (orderlines.length > 1) {
                            while (temp > 100) {
                                temp = parseInt(temp / orderlines.length);
                            }
                        }
                        var orderline_total = 0;
                        for (var i = 0; i < orderlines.length - 1; i++) {
                            var apply_disc_percen = (temp * 100) / 100;

                            var current_price = orderlines[i].get_display_price() - apply_disc_percen;
                            var diff = orderlines[i].price - current_price;
                            var apply_disc_percen6 = (diff * 100) / orderlines[i].price;
                            var discount = ((orderlines[i].get_display_price() * orderlines[i].quantity - current_price) / (orderlines[i].get_display_price() * orderlines[i].quantity)) * 100;

                            orderlines[i].set_global_discount(apply_disc_percen6);
                            orderlines[i].set_discount(apply_disc_percen6);
                            orderline_total = orderline_total + orderlines[i].get_display_price();
                        }

                        if (orderlines[orderlines.length - 1].get_discount()) {
                            orderlines[orderlines.length - 1].set_discount(0);
                            var total = self.env.pos.get_order().get_total_with_tax();

                            var order_total = self.env.pos.get_order().get_total_with_tax();
                            var apply_disc_percen = ((order_total - final_total) * 100) / orderlines[orderlines.length - 1].price;
                            orderlines[orderlines.length - 1].set_global_discount(apply_disc_percen);
                            orderlines[orderlines.length - 1].set_discount(apply_disc_percen);
                        } else {
                            var apply_disc_percen = ((self.env.pos.get_order().get_total_with_tax() - final_total) * 100) / orderlines[orderlines.length - 1].get_display_price();
                            orderlines[orderlines.length - 1].set_global_discount(apply_disc_percen);
                            orderlines[orderlines.length - 1].set_discount(apply_disc_percen);
                        }
                    } else {
                        var selected_orderline = self.env.pos.get_order().get_selected_orderline();
                        if (selected_orderline) {
                            if (selected_orderline.get_discount()) {
                                var price = selected_orderline.get_display_price();
                                var current_price = price - value;
                                var discount = ((selected_orderline.price * selected_orderline.quantity - current_price) / (selected_orderline.price * selected_orderline.quantity)) * 100;
                                if (selected_orderline.get_fix_discount()) {
                                    selected_orderline.set_total_discount(selected_orderline.get_total_discount() + parseFloat(value));
                                    selected_orderline.set_fix_discount(selected_orderline.get_fix_discount() + parseFloat(value));
                                } else {
                                    selected_orderline.set_total_discount(parseFloat(value));
                                    selected_orderline.set_fix_discount(parseFloat(value));
                                }
                                selected_orderline.set_global_discount(discount);
                                selected_orderline.set_discount(discount);
                            } else {
                                var apply_disc_percen = (value * 100) / selected_orderline.get_display_price();
                                selected_orderline.set_total_discount(parseFloat(value));
                                selected_orderline.set_fix_discount(parseFloat(value));
                                selected_orderline.set_global_discount(apply_disc_percen);
                                selected_orderline.set_discount(apply_disc_percen);
                            }
                        }
                    }
                }
                if (document.getElementById("discount_percentage_radio") && document.getElementById("discount_percentage_radio").checked) {
                    if (self.env.pos.is_global_discount) {
                        var orderlines = self.env.pos.get_order().get_orderlines();
                        if (self.env.pos.get_order().get_order_global_discount()) {
                            self.env.pos.get_order().set_order_global_discount(self.env.pos.get_order().get_order_global_discount() + parseFloat(value));
                        } else {
                            self.env.pos.get_order().set_order_global_discount(parseFloat(value));
                        }
                        _.each(orderlines, function (each_order_line) {
                            if (each_order_line.get_discount()) {
                                var price = each_order_line.get_display_price();

                                var current_price = price - (price * value) / 100;
                                var discount = ((each_order_line.price * each_order_line.quantity - current_price) / (each_order_line.price * each_order_line.quantity)) * 100;
                                each_order_line.set_global_discount(discount);
                                each_order_line.set_discount(discount);
                                each_order_line.set_total_discount(parseFloat(each_order_line.price) - parseFloat(each_order_line.get_display_price()));
                            } else {
                                each_order_line.set_global_discount(parseFloat(value));
                                each_order_line.set_discount(parseFloat(value));
                                each_order_line.set_total_discount(parseFloat(each_order_line.price) - parseFloat(each_order_line.get_display_price()));
                            }
                        });
                    } else {
                        var selected_orderline = self.env.pos.get_order().get_selected_orderline();
                        if (selected_orderline) {
                            if (selected_orderline.get_discount()) {
                                var price = selected_orderline.get_display_price();

                                var current_price = price - (price * value) / 100;
                                var discount = ((selected_orderline.price * selected_orderline.quantity - current_price) / (selected_orderline.price * selected_orderline.quantity)) * 100;

                                selected_orderline.set_global_discount(discount);
                                selected_orderline.set_discount(discount);
                                selected_orderline.set_total_discount(parseFloat(selected_orderline.price) - parseFloat(selected_orderline.get_display_price()));
                            } else {
                                selected_orderline.set_global_discount(parseFloat(value));
                                selected_orderline.set_discount(parseFloat(value));
                                selected_orderline.set_total_discount(parseFloat(selected_orderline.price) - parseFloat(selected_orderline.get_display_price()));
                            }
                        }
                    }
                }
                self.trigger("close-popup");
            }
        }
    }

    GlobalDiscountPopupWidget.template = "GlobalDiscountPopupWidget";
    Registries.Component.add(GlobalDiscountPopupWidget);
});
