odoo.define('pways_pos_lot_selection.ReceiptScreen', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ReceiptScreen = require('point_of_sale.ReceiptScreen');
	var rpc = require('web.rpc');
	const PwaysLotReceiptScreen = (ReceiptScreen) =>
		class extends ReceiptScreen {
			constructor() {
				super(...arguments);
				let self = this;
				let upd_qty = {};
				const order = this.currentOrder;
				let orderlines = order.get_orderlines();
				let config = this.env.pos.config;				
				$.each(orderlines, function( i, line ){
					let prd = line.product;
					if (prd.type == 'product' && line.lots_barcode.length > 0){
						if(prd.tracking == 'lot'){
							let lot_by_nm = self.env.pos.db.lot_barcode_by_name[line.lots_barcode[0].name]
							rpc.query({
							    model: 'stock.quant',
							    method: 'update_stock_quantity',
							    args: [lot_by_nm, line.quantity],
							}).then(function(result) {
							  console.log("Success")    
							});
							if(lot_by_nm){
								lot_by_nm.loc_qty -= line.quantity;
							}
						}
						if(prd.tracking == 'serial'){
							$.each(line.lots_barcode, function( l, lb ){
								let lot_by_nm = self.env.pos.db.lot_barcode_by_name[lb.name]
								if(lot_by_nm){
									lot_by_nm.loc_qty -= 1;
								}
							});
						}
					}
				});
			}
		};

	Registries.Component.extend(ReceiptScreen, PwaysLotReceiptScreen);

	return ReceiptScreen;

});
