odoo.define('pways_pos_lot_selection.productScreen', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ProductScreen = require('point_of_sale.ProductScreen'); 
	const NumberBuffer = require('point_of_sale.NumberBuffer');

	const PwaysProductScreen = (ProductScreen) =>
		class extends ProductScreen {
			constructor() {
				super(...arguments);
			}
			
			async _clickProduct(event) {
				let self = this;
				const product = event.detail;
				let allow_order = self.env.pos.config.pos_allow_order;
				let deny_order= self.env.pos.config.pos_deny_order || 0;
				let call_super = true;
				if(call_super){
					
					if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
						if (!this.currentOrder) {
							this.env.pos.add_new_order();
						}
						const product = event.detail;
						let price_extra = 0.0;
						let draftPackLotLines, weight, description, packLotLinesToEdit;

						if (this.env.pos.config.product_configurator && _.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
							let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
											  .filter((attr) => attr !== undefined);
							let { confirmed, payload } = await this.showPopup('ProductConfiguratorPopup', {
								product: product,
								attributes: attributes,
							});

							if (confirmed) {
								description = payload.selected_attributes.join(', ');
								price_extra += payload.price_extra;
							} else {
								return;
							}
						}

						// Gather lot information if required.
						if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
							const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
							if (isAllowOnlyOneLot) {
								packLotLinesToEdit = [];
							} else {
								const orderline = this.currentOrder
									.get_orderlines()
									.filter(line => !line.get_discount())
									.find(line => line.product.id === product.id);
								if (orderline) {
									packLotLinesToEdit = orderline.getPackLotLinesToEdit();
								} else {
									packLotLinesToEdit = [];
								}
							}
							let barcodes = this.env.pos.db.get_lot_barcode_by_prod_id(product.id);
							const { confirmed, payload } = await this.showPopup('EditListPopup', {
								title: this.env._t('Lot/Serial Number(s) Required'),
								isSingleItem: isAllowOnlyOneLot,
								array: packLotLinesToEdit,
								product : product,
								barcodes : barcodes,
							});
							if (confirmed) {
								// Segregate the old and new packlot lines
								const modifiedPackLotLines = Object.fromEntries(
									payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
								);
								const newPackLotLines = payload.newArray
									.filter(item => !item.id)
									.map(item => ({ lot_name: item.text }));

								draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
							} else {
								// We don't proceed on adding product.
								return;
							}
						}

						// Take the weight if necessary.
						if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
							// Show the ScaleScreen to weigh the product.
							if (this.isScaleAvailable) {
								const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
									product,
								});
								if (confirmed) {
									weight = payload.weight;
								} else {
									// do not add the product;
									return;
								}
							} else {
								await this._onScaleNotAvailable();
							}
						}
						// Add the product after having the extra information.
						this.currentOrder.add_product(product, {
							draftPackLotLines,
							description: description,
							price_extra: price_extra,
							quantity: weight,
						});
						NumberBuffer.reset();
					}
					else{
						super._clickProduct(event);
					}
				}
			}

			async _onClickPay() {
				let self = this;
				let order = this.env.pos.get_order();
				let lines = order.get_orderlines();
				let pos_config = self.env.pos.config; 
				let allow_order = pos_config.pos_allow_order;
				let deny_order= pos_config.pos_deny_order;
				let call_super = true;
				if(pos_config.pos_display_stock)
				{
					if (pos_config.show_stock_location == 'specific')
					{
						let partner_id = self.env.pos.get_client();
						let location = self.env.pos.locations;
						let prods = [];

						$.each(lines, function( i, line ){
							if (line.product.type == 'product'){
								prods.push(line.product.id)
							}
						});
						await this.rpc({
							model: 'stock.quant',
							method: 'get_products_stock_location_qty',
							args: [partner_id ? partner_id.id : 0, location,prods],
						}).then(function(output) {
							let flag = 0;
							for (let i = 0; i < lines.length; i++) {
								for (let j = 0; j < output.length; j++) {
									let values = $.map(output[0], function(value, key) { 
										let keys = $.map(output[0], function(value, key) {
											if (lines[i].product.type == 'product' && lines[i].product['id'] == key ){
												if (allow_order == false && lines[i].quantity > value){
													flag = flag + 1;
												}
												let check = value - lines[i].quantity;
												if (allow_order == true && deny_order > check){
													flag = flag + 1;
												}
											}
										});
									});
								}
							}
							if(flag > 0){
								call_super = false;  
								self.showPopup('ErrorPopup', {
									title: self.env._t('Denied Order'),
									body: self.env._t('Ordered qty of One or more product(s) is more than available qty.'),
								});
							}
						});
					} else {
						$.each(lines, function( i, line ){
							if (line.product.type == 'product'){
								if (allow_order == false && line.quantity > line.product['bi_on_hand']){
									call_super = false; 
									self.showPopup('ErrorPopup', {
										title: self.env._t('Denied Order'),
										body: self.env._t('Ordered qty of One or more product(s) is more than available qty.'),
									});
									return
								}
								let check = line.product['bi_on_hand'] - line.quantity;
								if(allow_order == true && check < deny_order){
									call_super = false; 
									self.showPopup('ErrorPopup', {
										title: self.env._t('Denied Order'),
										body: self.env._t('Ordered qty of One or more product(s) is more than available qty.'),
									});
									return
								}
							}
						});
					}
				}

				let has_valid_product_lot = _.every(lines, function(line){
					return line.has_valid_product_lot();
				});
				if(!has_valid_product_lot){
					call_super = false;  
					self.showPopup('ErrorPopup', {
						title: self.env._t('Empty Serial/Lot Number'),
						body: self.env._t('One or more product(s) required serial/lot number..'),
					});
					return
				}

				let lot_qty = {};
				$.each(lines, function( i, line ){
					let prd = line.product;
					if (prd.type == 'product' && 
						prd.tracking == 'lot' && line.lots_barcode.length > 0){
						let lot_name =line.lots_barcode[0].lot_name;
						if(lot_name in lot_qty){
							let old_qty = lot_qty[lot_name][1];
							lot_qty[lot_name] = [line.lots_barcode[0].loc_qty,line.quantity+old_qty]
						}else{
							lot_qty[lot_name] = [line.lots_barcode[0].loc_qty,line.quantity]
						}
						if(line.lots_barcode[0].loc_qty < line.quantity){
							call_super = false;  
							self.showPopup('ErrorPopup', {
								title: self.env._t('Invalid Lot Quantity'),
								body: self.env._t('Ordered qty of One or more product(s) is more than available qty.'),
							});
						}
					}
				});

				$.each(lot_qty, function( i, lq ){
					if (lq[1] > lq[0]){
						call_super = false;  
						self.showPopup('ErrorPopup', {
							title: self.env._t('Invalid Lot Quantity'),
							body: self.env._t('Ordered qty of One or more product(s) is more than available qty.'),
						});
					}
				});

				if(call_super){
					super._onClickPay();
				}
			}
		};

	Registries.Component.extend(ProductScreen, PwaysProductScreen);

	return ProductScreen;

});
