odoo.define('pways_pos_lot_selection.PwaysEditListPopup', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { useExternalListener } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const { useState } = owl.hooks;
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const EditListPopup = require('point_of_sale.EditListPopup');

	const PwaysEditListPopup = (EditListPopup) =>
		class extends EditListPopup {
			constructor() {
				super(...arguments);
			}

			get barcodes(){
				return this.props.barcodes;
			}

			async selectLot(event){
				var list_selected = new Array();
				$('.list-lines input, .list-lines select').each(
				    function(index){  
				        var input = $(this);
						list_selected.push(input.val());
				    }
				);
				let lot = $('.barcode_selector').val();
				let conditon = false;
				for (let i = 1; i < list_selected.length; i++) {
					if(list_selected[i] == lot){
						conditon = true
					}
				}
				if (conditon == true){
					this.showPopup("PwaysAlertPopUp", {
						'title': 'Duplicate Lot/Serial!',
						'body': lot + " Lot/Serial is already assigned."
					});
					NumberBuffer.reset();
				}
				else{
					$('.list-line-input:last').text(lot);
					let arr = this.state.array;
					arr[arr.length-1].text = lot;
					arr[arr.length-1].qty = 16;
				}
			}

			getPayload() {
				let self = this;
				let barcodes = this.barcodes;
				let lots = [];
				let res = true;
				$.each(barcodes, function( i, line ){
					lots.push(line.name)
				});
				let vals = {
					newArray: this.state.array
						.filter((item) => item.text.trim() !== '')
						.map((item) => Object.assign({}, item)),
				};				
				$.each(vals.newArray, function( i, line ){
					let is_valid = lots.indexOf(line.text);
					if(is_valid == -1 ){
						res = false;
						vals.newArray.splice(i, 1);
						alert("There are some invalid lot(s),Please add valid lot.")
					}
				});
				return vals;
			}

		}
	Registries.Component.extend(EditListPopup, PwaysEditListPopup);
	return PwaysEditListPopup;
});
