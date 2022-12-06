odoo.define('ob_pos_cash_in_out_partner.CustomCashMovePopup', function (require) {
    'use strict';

    var models = require('point_of_sale.models');

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    const { parse } = require('web.field_utils');
    const CashMovePopup = require('point_of_sale.CashMovePopup');
    const CustomCashMovePopup = (CashMovePopup) =>
		    class extends CashMovePopup {
		        constructor() {
				super(...arguments);
			}
        async confirm() {
        var partner_id = $('#cash_move_partners').val()
        this.partner_id = partner_id;
            try {
                parse.float(this.state.inputAmount);
            } catch (error) {
                this.state.inputHasError = true;
                this.errorMessage = this.env._t('Invalid amount');
                return;
            }
            if (this.state.inputType == '') {
                this.state.inputHasError = true;
                this.errorMessage = this.env._t('Select either Cash In or Cash Out before confirming.');
                return;
            }
            return super.confirm();
        }

        async getPayload() {
            return {
                amount: parse.float(this.state.inputAmount),
                reason: this.state.inputReason.trim(),
                type: this.state.inputType,
                partner_id: this.partner_id
            };
        }
		};
    Registries.Component.extend(CashMovePopup, CustomCashMovePopup);
	return CashMovePopup;
    });