odoo.define('pways_pos_lot_selection.models', function(require) {
	"use strict";

	var PosDB = require('point_of_sale.DB');
	var models = require('point_of_sale.models');
	var core = require('web.core');	
	var QWeb = core.qweb;
	var _t = core._t;
	
	models.load_fields('product.product', ['type']);
	models.load_models({
        model: 'stock.quant',
        fields: ['quantity','reserved_quantity','product_id','location_id','lot_id', 'reserve_quant', 'expiration_date', 'is_expired'],
        domain: function(self){ 
        	return [
        		['lot_id', '!=', false],
        		['location_id', '=', self.config.location_id[0]],
        		['quantity', '>', 0],
        		['is_expired', '=', false],
        	]; 
        },
        loaded: function(self, result)
        {
            let quants = [];
			let location = false;
			if(self.config.location_id){
				location = self.config.location_id[0];
			}

			result.forEach(function(quant) {
				var all_qty = {}
				var fullDate = new Date(Date.parse(quant.expiration_date));
				var twoDigitMonth = fullDate.getMonth() + 1 + "";
				if (twoDigitMonth.length == 1)
				    twoDigitMonth = "0" + twoDigitMonth;
				var twoDigitDate = fullDate.getDate() + "";
				if (twoDigitDate.length == 1)
				    twoDigitDate = "0" + twoDigitDate;
				var ExpDate = twoDigitDate + "/" + twoDigitMonth + "/" + fullDate.getFullYear();

				if(quant.reserve_quant <= quant.quantity){
					if(quant.is_expired == false){
						all_qty[location] = quant.quantity
						quant.all_qty = all_qty;
						quant.loc_qty = (quant.quantity - quant.reserve_quant);
						quant.name = quant.lot_id[1];
						quant.lot_name = quant.lot_id[1];
						quant.product_qty = quant.quantity;
						quant.expiration_date = ExpDate;
						quants.push(quant);
					}
				}
			});
            self.lot_barcodes = quants;
			self.db.add_barcode_lots(quants);
        },
    });

	PosDB.include({
		init: function(options){
			this._super(options);			
			this.lot_barcode_by_name = {};
			this.lot_barcode_by_id = {};
			this.lot_barcode_by_lotbrcd = {};
		},

		add_barcode_lots: function (barcode) {
			var self = this;
			barcode.forEach(function(brcd) {
				self.lot_barcode_by_name[brcd.name] = brcd;
				self.lot_barcode_by_id[brcd.id] = brcd;
				self.lot_barcode_by_lotbrcd[brcd.lot_name] = brcd;
			});
		},

		get_lot_barcode_by_lotbrcd: function(lot_name){
			if(this.lot_barcode_by_lotbrcd[lot_name]){
				return this.lot_barcode_by_lotbrcd[lot_name];
			} else {
				return undefined;
			}
		},

		get_lot_barcode_by_name: function(name){
			if(this.lot_barcode_by_name[name]){
				return this.lot_barcode_by_name[name];
			} else {
				return undefined;
			}
		},

		get_lot_barcode_by_id: function(id){
			if(this.lot_barcode_by_id[id]){
				return this.lot_barcode_by_id[id];
			} else {
				return undefined;
			}
		},

		get_lot_barcode_by_prod_id(id){
			let barcodes = this.lot_barcode_by_id;
			let brcd_lst = [];
			$.each(barcodes, function( i, line ){
				if (line.product_id[0] == id && line.loc_qty > 0){
					brcd_lst.push(line)
				}
			});
			return brcd_lst;
		},

	});

	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		scan_product: function(parsed_code) {
			var self = this;
			var res = _super_posmodel.scan_product.apply(this,arguments);
			var selectedOrder = this.get_order();
			var barcode = self.db.get_lot_barcode_by_lotbrcd(parsed_code.base_code);
			if(barcode && barcode.product_id && barcode.lot_name){
				var product = self.db.get_product_by_id(barcode.product_id[0]);
				if(product){
					let modifiedPackLotLines = {};
					let newPackLotLines = [{lot_name: barcode.name}];
					let draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
					selectedOrder.add_product(product, {draftPackLotLines,});
					return true;
				}
			}
			return res;
		},
	});

	var OrderlineSuper = models.Orderline.prototype;
	models.Orderline = models.Orderline.extend({

		initialize: function(attr, options) {
			this.lots = this.lots || [];
			this.lots_barcode = this.lots_barcode || [];
			OrderlineSuper.initialize.call(this,attr,options);
		},

		get_lot_barcodes : function () {
			return this.lots_barcode;
		},

		export_as_JSON: function() {
			var self = this;
			var json = OrderlineSuper.export_as_JSON.apply(this,arguments);
			var lots = [];
			var lot_brcd = [];

			$.each(self.pack_lot_lines.models, function( i, line ){
				lots.push(line.attributes.lot_name)
			});
			
			if(lots){
				let lot_barcodes = self.pos.lot_barcodes;
				$.each(lot_barcodes, function( i, line ){
					let is_valid = lots.indexOf(line.name);
					if(is_valid > -1 ){
						lot_brcd.push(line);
					}
					// console.log('JSONNNNNNNNNNN', lot_brcd);
				});
			}
			self.lots = lots;
			self.lots_barcode = lot_brcd || [];
			json.lots = lots|| [];
			json.lots_barcode = lot_brcd|| [];
			// console.log('JSONNNNNNNNNNN', json);
			return json;
		},
		
		init_from_JSON: function(json){
			OrderlineSuper.init_from_JSON.apply(this,arguments);
			this.lots = json.lots;
			this.lots_barcode = this.lots_barcode || [];
		},

		export_for_printing: function() {
			var json = OrderlineSuper.export_for_printing.apply(this,arguments);
			json.lots = this.lots || [];
			json.lots_barcode = this.lots_barcode || [];
			return json;
		},

	});

});