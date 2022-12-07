odoo.define('pos_internal_transfer', function (require) {
"use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { useState, useRef } = owl.hooks;
    const models = require('point_of_sale.models');


    models.load_models([{
        model: 'stock.picking.type',
        fields: ['id','name','display_name'],
        domain: function(self){ return [['code', '=', 'internal'],['warehouse_id.company_id', '=', self.company && self.company.id]]; }, 
        loaded: function(self, result){
            self.stockpickingtype = result;
        },
    },{
        model: 'stock.location',
        fields: ['id','name','display_name'],
        domain: function(self){ return [['id','in',self.config.allow_internal_locations]]; },
        loaded: function(self, result){
            self.stocklocations = result;
        },
    }]);


    class InternalTransferButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            var orderlines = this.env.pos.get('selectedOrder').get_orderlines();
            if(orderlines.length > 0){
                await this.showPopup('InternalTransferPopupWidget');
            }
            else{
                alert("Please add some products.");
            }
        }
    }
    InternalTransferButton.template = 'InternalTransferButton';

    ProductScreen.addControlButton({
        component: InternalTransferButton,
        condition: function() {
            return this.env.pos.config.allow_internal_locations;
        },
    });

    Registries.Component.add(InternalTransferButton);

    class InternalTransferPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.inputRef = useRef('input');
            this.changes = {};
        }

        async confirm_transfer(event) {
            var self = this.env;
            var self2 = this;
            var order =this.env.pos.get('selectedOrder');
            var picking_type = $('.pick-type').val();
            var source_location = $('.pick-src').val();
            var dest_location = $('.pick-dest').val();
            var state = $('.pick-state').val();
            if(parseInt(source_location) == parseInt(dest_location)){
                alert("You are not allowed to choose same location as source and destination.")
            }
            else{
                var product_list = []
                var lines = order.get_orderlines();
                for(var i=0;i<lines.length;i++){
                    var prod_exist = $.grep(product_list, function(val) {
                        return val.product_id === lines[i].product.id;
                    });
                    if(prod_exist.length!=0){
                        prod_exist[0]['quantity'] += lines[i].quantity
                    }
                    else{
                        product_list.push({
                            'product_id': lines[i].product.id,
                            'quantity': lines[i].quantity
                        });
                    }
                }
                var client = false;
                if (self.pos.get_client()){
                    client = self.pos.get_client().id;
                }
                var company_id = self.pos.company.id;
                var data = [client,picking_type,source_location,dest_location,state,product_list,company_id];
                this.rpc({
                      model: 'pos.session',
                      method: 'create_stock_picking',
                      args: data,
                }).then(function (result) {
                    alert("Your Picking number is : "+result)
                    self.pos.delete_current_order();
                    self2.trigger('close-popup');  
                });
            }
                      
        }
    }
    InternalTransferPopupWidget.template = 'InternalTransferPopupWidget';
    Registries.Component.add(InternalTransferPopupWidget);
});

