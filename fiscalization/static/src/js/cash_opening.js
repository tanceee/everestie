odoo.define('CashOpeningPopupExtend', function(require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const { useState, useRef } = owl.hooks;

    const CashOpeningPopup = require("point_of_sale.CashOpeningPopup")

    const FiscalizationCashOpeningPopup = CashOpeningPopup => class extends CashOpeningPopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                is_initial_cash: true,
            });
        }

        startSession() {
            this.env.pos.bank_statement.balance_start = this.state.openingCash;
            this.env.pos.pos_session.state = 'opened';
            var self = this 
            this.rpc({
                   model: 'pos.session',
                    method: 'set_cashbox_pos',
                    args: [this.env.pos.pos_session.id, this.state.openingCash, this.state.notes, this.state.is_initial_cash],
                }).then(function(res){
                    console.log("res", res)
                    var res = JSON.parse(res)
                    if(res.response == "OK"){
                        $("#cash_reg_res").html(`<span style='color:green'>${res.response}</span>`)

                        self.cancel();
                    }
                    else{
                        console.error(res.response)
                        $("#cash_reg_res").html(`<span style='color:red'>${res.response}</span>`)
                    }
                })
        }
    }

    Registries.Component.extend(CashOpeningPopup, FiscalizationCashOpeningPopup);


});