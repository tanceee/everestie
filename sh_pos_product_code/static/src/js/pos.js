odoo.define('sh_pos_product_code.pos', function(require) {
    'use strict';
    
    var models = require('point_of_sale.models')

    var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function () {
            var res = _super_Orderline.export_for_printing.apply(this, arguments)
            if(this.get_product().default_code){
                res['product_default_code'] = this.get_product().default_code;
            }
            return res
        }
    })

});