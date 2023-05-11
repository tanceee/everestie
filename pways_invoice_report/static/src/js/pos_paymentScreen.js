odoo.define("pos_qr_show.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const { isConnectionError } = require('point_of_sale.utils');


    const PosQRShowPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
            super(...arguments);
            this.invoice_report = false;
            this.invoice_detais = false;
            if (this.env.pos.config.enable_invoice_selection === 'default_invoice') {this.toggleIsinvoice_report();}
            if (this.env.pos.config.enable_invoice_selection === 'default_detail') {this.toggleIsinvoicedetails_report();}
        }


        toggleIsinvoice_report() {
            if (this.invoice_report == true) {
               this.invoice_report = false;
            }
            else {
                this.invoice_report = true;
            }
            this.render();
        }

        toggleIsinvoicedetails_report() {
            if (this.invoice_detais == true) {
               this.invoice_detais = false;
            }
            else {
                this.invoice_detais = true;
            }
            this.render();
        }

        async _finalizeValidation() {
            if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];
            try {
                if (this.currentOrder.is_to_invoice()) {
                    if (this.invoice_report & this.invoice_detais){
                        syncedOrderBackendIds = await this.env.pos.invoice_report_multiple(
                        this.currentOrder);
                    }
                    else if (this.invoice_report){
                        syncedOrderBackendIds = await this.env.pos.invoice_report(
                        this.currentOrder
                        );
                    }
                    else if (this.invoice_detais){
                        syncedOrderBackendIds = await this.env.pos.invoice_detais(
                        this.currentOrder
                        );
                    } else{
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                            this.currentOrder
                        );
                    }
                } else {
                    syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                }
            } catch (error) {
                if (error.code == 700 || error.code == 701)
                    this.error = true;

                if ('code' in error) {
                    // We started putting `code` in the rejected object for invoicing error.
                    // We can continue with that convention such that when the error has `code`,
                    // then it is an error when invoicing. Besides, _handlePushOrderError was
                    // introduce to handle invoicing error logic.
                    await this._handlePushOrderError(error);
                } else {
                    // We don't block for connection error. But we rethrow for any other errors.
                    if (isConnectionError(error)) {
                        this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Connection Error'),
                            body: this.env._t('Order is not synced. Check your internet connection'),
                        });
                    } else {
                        throw error;
                    }
                }
            }
            if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                const result = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncedOrderBackendIds
                );
                if (!result) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Error: no internet connection.'),
                        body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                    });
                }
            }

            this.showScreen(this.nextScreen);

            // If we succeeded in syncing the current order, and
            // there are still other orders that are left unsynced,
            // we ask the user if he is willing to wait and sync them.
            if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }
           
    };


    Registries.Component.extend(PaymentScreen, PosQRShowPaymentScreen);

    return PaymentScreen;
});
