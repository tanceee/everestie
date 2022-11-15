odoo.define("sh_pos_order_discount.pos", function (require) {
    var models = require("point_of_sale.models");

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.global_discount;
            this.fix_discount;
            this.total_discount;
            _super_orderline.initialize.call(this, attr, options);
        },
        set_global_discount: function (discount) {
            this.global_discount = discount;
        },
        get_global_discount: function () {
            return this.global_discount;
        },
        set_fix_discount: function (discount) {
            this.fix_discount = discount;
        },
        get_fix_discount: function () {
            return this.fix_discount;
        },
        get_sh_discount_str: function () {
            return this.discount.toFixed(2);
        },
        set_total_discount: function (discount) {
            this.total_discount = discount;
        },
        get_total_discount: function () {
            return this.total_discount || false;
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            this.order_global_discount;
            //    		this.order_total_discount;
            _super_order.initialize.call(this, attr, options);
        },
        set_order_global_discount: function (discount) {
            this.order_global_discount = discount;
        },
        get_order_global_discount: function () {
            return this.order_global_discount || false;
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            var self = this;
            _super_posmodel.initialize.apply(this, arguments);
            this.is_global_discount = false;
        },
    });
});
