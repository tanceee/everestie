odoo.define('pways_pos_lot_selection.Screen', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var utils = require('web.utils');
	var core = require('web.core');
	var _t = core._t;
	var QWeb = core.qweb;

	screens.ReceiptScreenWidget.include({
		show: function () {
			this._super(); 
			var order = this.pos.get_order();                     
			var self = this;
			var orderlines = order.get_orderlines();
			$.each(orderlines, function( i, line ){
				var prd = line.product;
				if (prd.type == 'product' && line.lots_barcode.length > 0){
					if(prd.tracking == 'lot'){
						var lot_by_nm = self.pos.db.lot_barcode_by_name[line.lots_barcode[0].name]
						if(lot_by_nm){
							lot_by_nm.product_qty -= line.quantity;
						}
					}
					if(prd.tracking == 'serial'){
						$.each(line.lots_barcode, function( l, lb ){
							var lot_by_nm = self.pos.db.lot_barcode_by_name[lb.name]
							if(lot_by_nm){
								lot_by_nm.product_qty -= 1;
							}
						});
					}
				}
			});
		},
	});
	

	screens.ActionpadWidget.include({
		renderElement: function() {
			var self = this;
			this._super();
			this.$('.pay').click(function(ev){
				var order = self.pos.get_order();
				let lines = order.get_orderlines();
				var call_super = true;  
				var has_valid_product_lot = _.every(order.orderlines.models, function(line){
					return line.has_valid_product_lot();
				});
				if(!has_valid_product_lot){
					call_super = false;  
					self.gui.show_popup('error',{
						'title': _t('Empty Serial/Lot Number'),
						'body':  _t('One or more product(s) required serial/lot number.'),
						cancel: function(){
							self.gui.show_screen('products');
						},
					});
				}
				$.each(lines, function( i, line ){
					let prd = line.product;
					if (prd.type == 'product' && 
						prd.tracking == 'lot' && line.lots_barcode.length > 0){
						if(line.lots_barcode[0].product_qty < line.quantity){
							call_super = false;  
							self.gui.show_popup('error',{
								'title': _t('Invalid Lot Quantity'),
								'body':  _t('Ordered qty of One or more product(s) is more than available qty..'),
								cancel: function(){
									call_super = false;  
									self.gui.show_screen('products');
								},
							});
						}
					}
				});
				if(call_super){
					self.gui.show_screen('payment');
				}											
			});
			this.$('.set-customer').click(function(){
				self.gui.show_screen('clientlist');
			});
			
		},
	});  
	
	
});
