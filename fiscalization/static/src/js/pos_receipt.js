odoo.define('fiscalization', function (require) {
    'use strict';
    const models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { isConnectionError } = require('point_of_sale.utils');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var rpc = require('web.rpc');
    var interval = []
    var isAlive = true
    var hasEnoughSpeed = true
    var conSpeed

    models.load_fields("pos.payment.method", ['create_e_invoice']);
    models.load_fields("pos.order", ['skip_pos_fisclization_only']);

    models.load_fields("res.users", ['operator_code']);

    models.load_fields("res.partner", ['is_transporter', 'license_plate_no']);
    // models.load_fields("operating.unit", ['partner_id']);

    models.load_fields("res.company", ['p12_certificate', 'invoice_check_endpoint', 'software_code', 'certificate_password']);

    models.load_models([{
        model: 'operating.unit',
        fields: ['name', 'partner_id', 'address', 'code'],
        domain: function (self) { return [['id', '=', self.config.operating_unit_id[0]]] },
        loaded: function (self, operating_units) {
            self.business_unit_address = operating_units[0].address
            self.code = operating_units[0].address

            //            partner_id = self.db.get_partner_by_id(partner_id)
            //            self.business_unit_address = address;
        },
    }], { "after": "pos.config" })

    var _super = models.Order;
    var _superPosModel = models.PosModel;
    var _posmodel_super = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        initialize: function () {
            _posmodel_super.initialize.apply(this, arguments);
            this.ready.then(() => {
                this.disable_fiscalization = this.config.disable_fiscalization
            });
        },
    });

    const ProductScreenCustom = ProductScreen => class extends ProductScreen {
        async _onClickPay() {
            var skip_pos_fisclization_only = this.currentOrder.is_skip_pos_fisclization_only()
            if (skip_pos_fisclization_only && this.env.pos.config.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = true
            }
            else if (!skip_pos_fisclization_only && this.env.pos.config.disable_fiscalization == true && this.env.pos.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = false
            }
            else if (this.env.pos.config.disable_fiscalization == true && this.env.pos.disable_fiscalization == false) {
                this.env.pos.config.disable_fiscalization = false
            }
            super._onClickPay()
        }
    }

    const PosPaymentScreenCustom = (PaymentScreen) => class extends PaymentScreen {
        addNewPaymentLine({ detail: paymentMethod }) {
            const order = this.env.pos.get_order();

            if (this.paymentLines.length) {
                var create_e_invoice = false
                var method_name = ""
                for (let index = 0; index < this.paymentLines.length; index++) {
                    const paymentLine = this.paymentLines[index];
                    if (paymentLine.payment_method.create_e_invoice) {
                        create_e_invoice = true
                        method_name = paymentLine.payment_method.name
                    }
                }
                if (create_e_invoice && !paymentMethod.create_e_invoice) {
                    alert(`${paymentMethod.name} payment method can not be used with ${method_name}, It will create a E-Invoice.`)
                    return
                }
                if (!create_e_invoice && paymentMethod.create_e_invoice) {
                    alert(`${paymentMethod.name} payment method can only be used with E-Invoice methods, It will create a E-Invoice.`)
                    return
                }
            }
            else {
                if (paymentMethod.create_e_invoice && this.currentOrder.is_to_invoice() && !this.currentOrder.skip_fiscalization) {
                    this.currentOrder.set_to_skip_pos_fisclization_only(true);
                }
                else {
                    this.currentOrder.set_to_skip_pos_fisclization_only(false);

                }

            }

            super.addNewPaymentLine(...arguments);

        }

        toggleIsToInvoice() {
            super.toggleIsToInvoice(...arguments);
            var create_e_invoice = false

            for (let index = 0; index < this.paymentLines.length; index++) {
                const paymentLine = this.paymentLines[index];
                if (paymentLine.payment_method.create_e_invoice) {
                    create_e_invoice = true
                }
            }
            if (this.currentOrder.is_to_invoice() && create_e_invoice && !this.currentOrder.skip_fiscalization){
                this.currentOrder.set_to_skip_pos_fisclization_only(true);
            }
            if (!this.currentOrder.is_to_invoice() && create_e_invoice) {
                this.currentOrder.set_to_skip_pos_fisclization_only(false);

            }


        }
    }
    Registries.Component.extend(PaymentScreen, PosPaymentScreenCustom);
    Registries.Component.extend(ProductScreen, ProductScreenCustom);


    models.Order = models.Order.extend({
        //@Override
        initialize: function (attributes, options) {
            _super.prototype.initialize.apply(this, arguments);

            if (options.json) {
            }
            else {
                this.nslf = false
                this.nivf = false
                this.iic_code = false
                this.business_unit_code = false
                this.operator_code = false
                this.business_unit_address = false
                this.qrcode = false
                this.transporter = false
                this.license = false
                this.delivery_datetime = false
                this.push_datetime = false
                this.skip_pos_fisclization_only = false

            }
        },

        //@Override
        export_for_printing: function () {
            var receipt = _super.prototype.export_for_printing.apply(this, arguments);
            if (this.pos.config.disable_fiscalization == false) {
                var qrcode = this.qrcode
                if (!qrcode) {
                    var qrtext = this.fiscalization_url + "?iic=" + this.nslf + "&tin=" + this.pos.company.vat + "&crtd=" + this.invoice_issue_date_time + "&prc=" + this.amount_total_formatted;
                    var qr = new QRious({
                        size: 100,
                    });
                    qr.set({
                        foreground: 'black',
                        value: qrtext
                    });
                    qrcode = qr.toDataURL('image/png')
                }
                receipt.qrcode = qrcode
                receipt.nslf = this.nslf
                receipt.nivf = this.nivf
                var transporter = ""
                if (this.transporter) {
                    transporter = this.pos.db.get_partner_by_id(this.transporter).name
                }
                receipt.transporter = transporter
                receipt.license = this.license

                var formatted_delivery_datetime = ""
                if (this.delivery_datetime) {
                    var delivery_datetime = new Date(this.delivery_datetime);
                    formatted_delivery_datetime = field_utils.format.datetime(
                        moment(delivery_datetime), {}, { timezone: false });
                }
                receipt.delivery_datetime = formatted_delivery_datetime
                // console.log(">>>>>>>>>>>>123", receipt, this)
                receipt.business_unit_code = this.business_unit_code
                receipt.tcr_code = this.pos.config.tcr_code
                receipt.operator_code = this.operator_code

            }
            return receipt
        },

        //@Override
        init_from_JSON: function (json) {
            if (this.pos.config.disable_fiscalization == false) {
                this.nslf = json.nslf
                this.nivf = json.nivf
                this.iic_code = json.iic_code
                this.business_unit_code = json.business_unit_code
                this.operator_code = json.operator_code
                this.business_unit_address = json.business_unit_address
                this.fiscalization_url = json.fiscalization_url
                this.invoice_issue_date_time = json.invoice_issue_date_time
                this.amount_total_formatted = json.amount_total_formatted
                this.transporter = json.transporter
                this.license = json.license
                this.delivery_datetime = json.delivery_datetime
                this.push_datetime = json.push_datetime
                this.skip_pos_fisclization_only = json.skip_pos_fisclization_only

            }
            _super.prototype.init_from_JSON.apply(this, arguments);

        },

        //@Override
        export_as_JSON: function () {
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            if (this.pos.config.disable_fiscalization == false) {
                json.iic_code = this.iic_code
                json.transporter = this.transporter
                json.license = this.license
                json.delivery_datetime = this.delivery_datetime
                json.push_datetime = this.push_datetime

            }
            json.skip_pos_fisclization_only = this.skip_pos_fisclization_only

            return json
        },
        set_to_skip_pos_fisclization_only: function (skip_pos_fisclization_only) {
            this.assert_editable();

            this.skip_pos_fisclization_only = skip_pos_fisclization_only;
            if (skip_pos_fisclization_only && this.pos.config.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = true
            }
            else if (!skip_pos_fisclization_only && this.pos.config.disable_fiscalization == true && this.pos.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = false
            }
            else if (this.pos.config.disable_fiscalization == true && this.pos.disable_fiscalization == false) {
                this.pos.config.disable_fiscalization = false
            }
        },

        is_skip_pos_fisclization_only: function () {
            return this.skip_pos_fisclization_only;
        },

        //@Override
        initialize_validation_date: function () {
            _super.prototype.initialize_validation_date.apply(this, arguments);
            // var validation_date = new Date();
            if (this.pos.config.disable_fiscalization == false) {
                this.push_datetime = time.datetime_to_str(new Date())
                //  *************** ORDER IIC *********************
                if (!this.iic_code) {
                    var p12_file = this.pos.company.p12_certificate
                    var certificate_password = this.pos.company.certificate_password
                    if (!p12_file || !certificate_password) {
                        alert("p12 Cretificate / password issue!")
                    }
                    var iic_message = this.generateIICMessage()
                    this.generateIIC(p12_file, certificate_password, iic_message)
                }
            }
            // ================================================
        },


        getOrderPushTime: function () {
            var self = this
            var min_order_post_time = 7500
            var all_order_count = 1

            var line_count = self.get_orderlines().length
            var time_taken = line_count / 20
            if (time_taken < 1) {
                time_taken = 7500
            }
            else {
                time_taken = parseInt(time_taken * 7500)
            }
            // let 20 lines take 7500 ms
            min_order_post_time = time_taken
            var request_timeout = (7500 * all_order_count) + min_order_post_time
            return request_timeout
        },


        generateIIC: function (file, password, message) {
            var self = this;
            var pkcs12Der = forge.util.decode64(file);
            var pkcs12Asn1 = forge.asn1.fromDer(pkcs12Der);
            var pkcs12 = forge.pkcs12.pkcs12FromAsn1(pkcs12Asn1, false, password);
            var privateKey
            for (var sci = 0; sci < pkcs12.safeContents.length; ++sci) {
                var safeContents = pkcs12.safeContents[sci];
                for (var sbi = 0; sbi < safeContents.safeBags.length; ++sbi) {
                    var safeBag = safeContents.safeBags[sbi];
                    if (safeBag.type === forge.pki.oids.keyBag) {
                        privateKey = safeBag.key;
                    } else if (safeBag.type === forge.pki.oids.pkcs8ShroudedKeyBag) {
                        privateKey = safeBag.key;
                    } else if (safeBag.type === forge.pki.oids.certBag) { }
                }
            }
            //*************/ New Updated Code 22 July 2021 /*************//
            var sha256 = forge.md.sha256.create();
            sha256.update(message, 'utf8');
            var signature = privateKey.sign(sha256);

            var md5 = forge.md.md5.create();
            md5.update((signature));
            // IIC generated
            var IIC = md5.digest().toHex().toUpperCase()
            self.iic_code = IIC;
            // ************ End****************************
        },


        generateIICMessage: function () {
            var self = this
            var vat = self.pos['company']['vat'];
            var toUTC = moment(new Date(self.formatted_validation_date)).format("YYYY-MM-DDTHH:mm:ss") + "+02:00";
            var order_name = self.name
            var soft_code = self.pos['company']['software_code'];
            var business_unit_code = self.pos['config']['business_unit_code'];
            var tcr_code = self.pos['config']['tcr_code'];
            // var operator_code = self.pos.get_cashier().operator_code
            var total_amount = self.export_for_printing().total_with_tax
            // create message
            var message = vat + '|' + toUTC + '|' + order_name + '|' + business_unit_code + '|' + tcr_code + '|' + soft_code + '|' + total_amount
            return message
        },


        getOrderQRCode: function () {
            var self = this
            var total_amount = self.export_for_printing().total_with_tax
            var fiscalization_url = self.pos['company']['invoice_check_endpoint'];
            // var vat = self.pos['company']['vat'];
            var toUTC = moment(new Date(self.creation_date)).format("YYYY-MM-DDTHH:mm:ss") + "+02:00";
            var iic = self.iic_code
            var qr = new QRious({
                size: 125,
            });

            var qrtext = fiscalization_url + "?iic=" + iic + "&tin=" + self.pos['company']['vat'] + "&crtd=" + toUTC + "&prc=" + total_amount;

            qr.set({
                foreground: 'black',
                size: 125,
                value: qrtext
            });

            return qr.toDataURL('image/png')
        },
    });


    models.PosModel = models.PosModel.extend({
        //@Override
        push_single_order: function (order, opts) {
            if (order && this.config.disable_fiscalization == false) {
                opts = opts || {};
                const self = this;
                const order_id = self.db.add_order(order.export_as_JSON());
                var current_order = undefined
                return new Promise((resolve, reject) => {
                    self.flush_mutex.exec(async () => {
                        const order = self.db.get_order(order_id);
                        try {
                            var order_list = self.get_order_list()
                            for (var i = 0, len = order_list.length; i < len; i++) {
                                if (order_list[i].uid === order_id) {
                                    current_order = order_list[i];
                                }
                            }
                            // //  *************** ORDER IIC *********************
                            // if (order && !order.data.iic_code) {
                            //     if (current_order) {
                            //         console.log("SELF", current_order, order)
                            //         var p12_file = self.company.p12_certificate
                            //         var certificate_password = self.company.certificate_password
                            //         if (!p12_file || !certificate_password) {
                            //             alert("p12 Cretificate / password issue!")
                            //         }
                            //         var iic_message = current_order.generateIICMessage()
                            //         current_order.generateIIC(p12_file, certificate_password, iic_message)
                            //         // current_order.save_to_db();
                            //         order.data.iic_code = current_order.iic_code
                            //     }
                            // }
                            // // ================================================
                            if (isAlive && hasEnoughSpeed) {
                                opts.timeout = current_order.getOrderPushTime()
                                resolve(await self._flush_orders([order], opts).then(async function (posted_orders) {
                                    return posted_orders
                                }));
                            }
                            else {
                                self.set_synch('disconnected', order.length);
                                resolve([])
                            }
                        }
                        catch (error) {
                            reject(error);
                        }
                    });
                });
            }
            else {
                return _superPosModel.prototype.push_single_order.apply(this, arguments);
                // super.push_single_order(...arguments)
            }
        },
    });



    const FiscalizationProductScreen = ProductScreen => class extends ProductScreen {
        //@Override
        constructor() {
            super(...arguments);
            if (this.env.pos.config.disable_fiscalization == false) {
                const checkOnlineStatus = async () => {
                    try {
                        const online = await fetch("/is-alive");
                        return online.status >= 200 && online.status < 300; // either true or false
                    } catch (err) {
                        hasEnoughSpeed = false
                        conSpeed = 0
                        return false; // definitely offline
                    }
                };

                setInterval(async () => {
                    const result = await checkOnlineStatus();
                    isAlive = result
                }, 6000); // probably too often, try 30000 for every 30 seconds

                // ******* For Connection speed test *******//
                const checkConnectionSpeed = async () => {

                    var self = this;
                    var imageAddr = "/fiscalization/static/src/img/1.png";
                    var downloadSize = 17372 //51329 //762934; //bytes

                    var startTime, endTime;
                    var download = new Image();
                    var speedKbps = 0
                    var myInterval
                    download.onload = function () {
                        endTime = (new Date()).getTime();
                        speedKbps = showResults();
                        conSpeed = speedKbps
                        // console.log("speedKbps >>>>>>>>>>>>>>>>>", speedKbps)
                        if (speedKbps > 200) {
                            //                            if (!hasEnoughSpeed) {
                            //                                $.notify('Connection Restored', "success");
                            //                            }
                            hasEnoughSpeed = true
                        }
                        else {
                            // console.log(">>>>>>>>>>>>>>LOAD FAILED")
                            //                            if (hasEnoughSpeed) {
                            //                                $.notify('Connection is Down, You will face delay in order fiscalization!', "warn");
                            //                            }
                            hasEnoughSpeed = false

                        }
                        var iter = 0
                        interval.forEach((inter => {
                            iter += 1
                            if (iter < interval.length) {
                                clearInterval(inter)
                            }
                            else {
                                return true
                            }
                        }));
                        // console.log("checkConnectionSpeed............", speedKbps)
                        // clearInterval(myInterval);
                        // self.postOnlineOrder(speedKbps)
                    }

                    download.onerror = function (err, msg) {
                        // console.error("ERROR: ", err, msg)
                        //                        $.notify('Network Offline, Order will not fiscalize!', "warn");
                        // ShowProgressMessage("Invalid image, or error downloading");
                    }

                    startTime = (new Date()).getTime();
                    var cacheBuster = "?nnn=" + startTime;
                    download.src = imageAddr + cacheBuster;

                    function showResults() {
                        var duration = (endTime - startTime) / 1000;
                        var bitsLoaded = downloadSize * 8;
                        var speedBps = (bitsLoaded / duration).toFixed(2);
                        var speedKbps = (speedBps / 1024).toFixed(2);
                        var speedMbps = (speedKbps / 1024).toFixed(2);
                        // console.log("SPEED>>>>>>>>> in KB", speedKbps, speedMbps)
                        // ShowProgressMessage([
                        //     "Your connection speed is:",
                        //     speedBps + " bps",
                        //     speedKbps + " kbps",
                        //     speedMbps + " Mbps"
                        // ]);
                        return speedKbps
                    }
                };

                interval.push(setInterval(async () => {
                    // console.log(">>> CHECK SPEED", isAlive)
                    if (isAlive) {
                        await checkConnectionSpeed();
                    }
                }, 30000)); // probably too often, try 30000 for every 30 seconds

            }
            else {
                isAlive = true
                hasEnoughSpeed = true
            }
        }
    }


    const FiscalizationPaymentScreen = PaymentScreen => class extends PaymentScreen {
        //@Override
        async _finalizeValidation() {
            console.log(">>>>>>>>>>>>>>>>>>>>>>>>_finalizeValidation", this.env.pos.config.disable_fiscalization)
            if (this.env.pos.config.disable_fiscalization == false) {
                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

                let syncedOrderBackendIds = [];

                try {

                    if (this.currentOrder.is_to_invoice()) {
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(this.currentOrder);
                    }
                    else {
                        syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                        // console.log("syncedOrderBackendIds -------------------->", syncedOrderBackendIds)
                    }

                }
                catch (error) {
                    if (error.code == 700)
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

                // this.showScreen(this.nextScreen);
                this._fiscalization()

                //     this.showScreen(this.nextScreen);
                // }
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
            else {
                super._finalizeValidation()
            }
        }


        async _fiscalization() {
            var self = this;
            // var data = this.currentOrder.getOrderReceiptEnv()
            // var receipt = data.receipt
            if (self.env.pos.config.disable_fiscalization == false) {
                // var total_amount = data['receipt']['total_with_tax'];
                // var vat = self.env.pos['company']['vat'];
                // var header_time = data['order']['formatted_validation_date'];
                // var order_name = data['order']['name'];
                // var soft_code = self.env.pos['company']['software_code'];
                var business_unit_code = self.env.pos['config']['business_unit_code'];
                var business_unit_address = self.env.pos.business_unit_address
                // var tcr_code = self.env.pos['config']['tcr_code'];
                var operator_code
                var cashier = self.env.pos.get_cashier()
                for (let index = 0; index < self.env.pos.users.length; index++) {
                    var usr = self.env.pos.users[index];
                    if (usr.id == cashier.user_id[0]) {
                        operator_code = usr.operator_code
                        break;
                    }
                }
                var order = self.env.pos.get_order();
                if (isAlive && hasEnoughSpeed) {
                    rpc.query({
                        model: 'pos.order',
                        method: 'search_read',
                        domain: [['pos_reference', '=', order['name']]],
                        fields: ['fic', 'partner_id']
                    })
                        .then(function (fetched_order) {
                            if (fetched_order.length) {
                                order.nslf = order['iic_code'];
                                order.nivf = fetched_order[0]['fic'];
                                order.business_unit_code = business_unit_code;
                                order.operator_code = operator_code;
                                order.business_unit_address = business_unit_address
                                order.qrcode = order.getOrderQRCode()
                                self.showScreen(self.nextScreen);
                            }
                            else {
                                //                    // offline 
                                order.nslf = order.iic_code
                                order.business_unit_code = business_unit_code;
                                order.operator_code = operator_code;
                                order.business_unit_address = business_unit_address
                                order.qrcode = order.getOrderQRCode()
                                self.showScreen(self.nextScreen);
                            }
                        })

                        .catch(function (type, error) {
                            order.nslf = order.iic_code
                            order.business_unit_code = business_unit_code;
                            order.operator_code = operator_code;
                            order.business_unit_address = business_unit_address
                            order.qrcode = order.getOrderQRCode()
                            self.showScreen(self.nextScreen);
                        });
                }
                else {
                    //                    // offline 
                    order.nslf = order.iic_code
                    order.business_unit_code = business_unit_code;
                    order.operator_code = operator_code;
                    order.business_unit_address = business_unit_address
                    order.qrcode = order.getOrderQRCode()
                    self.showScreen(self.nextScreen);
                }
            }
        }
    }


    Registries.Component.extend(ProductScreen, FiscalizationProductScreen);

    Registries.Component.extend(PaymentScreen, FiscalizationPaymentScreen);

});
