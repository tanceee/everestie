odoo.define('product_pricelist_matrix.generate_pricelist_matrix', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var FieldMany2ManyTags = require('web.relational_fields').FieldMany2ManyTags;
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
    var session = require('web.session');
    var QWeb = core.qweb;
    var _t = core._t;
    var ajax = require('web.ajax');

    var GeneratePriceListMatrix = AbstractAction.extend(StandaloneFieldManagerMixin, {
        hasControlPanel: true,

        /**
         * @override
         */
        init: function (parent, params) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.context = params.context;
            // in case the window got refreshed
            if (params.params && params.params.active_ids && typeof (params.params.active_ids === 'string')) {
                try {
                    this.context.active_ids = params.params.active_ids.split(',').map(id => parseInt(id));
                    this.context.active_model = params.params.active_model;
                } catch (e) {
                    console.log('unable to load ids from the url fragment 🙁');
                }
            }
            if (!this.context.active_model) {
                // started without an active module, assume product templates
                this.context.active_model = 'product.template';
            }
            this.fetch_default_pricelist()
        },
        /**
         * @override
         */
        willStart: function () {
            var self = this
            const fieldSetup =
                this.model.makeRecord('report.product_pricelist_matrix.report_pricelist', [{
                    name: 'pricelist_id',
                    type: 'many2many',
                    relation: 'product.pricelist',
                }])

                    .then(recordID => {
                        var record = self.model.get(recordID);
                        var options = {
                            mode: 'edit',
                        };
                        self.many2manytags = new FieldMany2ManyTags(self, 'pricelist_id', record, options);
                        self.many2manytags.nodeOptions.create = false;
                        self._registerWidget(recordID, 'pricelist_id', self.many2manytags);
                    });
            return Promise.all([fieldSetup, this._getHtml(), this._super()]);
        },

        fetch_default_pricelist: function () {
            var self = this;
            return self._rpc({
                route: '/product_pricelist_matrix/fetch_default_pricelist',
                params: { context: session.user_context, },
            }).then(function (result) {
                self.context.default_pricelist = result.default_pricelist;
            }, { shadow: true });
        },

        /**
         * @override
         */
        start: function () {
            this.controlPanelProps.cp_content = this._renderComponent();
            return this._super.apply(this, arguments).then(() => {
                this.$('.o_content').html(this.reportHtml);
            });
        },
        /**
         * Include the current model (template/variant) in the state to allow refreshing without losing
         * the proper context.
         * @override
         */
        getState: function () {
            return {
                active_model: this.context.active_model,
            };
        },
        getTitle: function () {
            return _t('Pricelist Matrix Report');
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Returns the expected data for the report rendering call (html or pdf)
         *
         * @private
         * @returns {Object}
         */
        _prepareActionReportParams: function () {
            var default_pricelist = null
            if (this.context.default_pricelist) {
                default_pricelist = [this.context.default_pricelist[0]["id"]]
            }
            return {
                active_model: this.context.active_model,
                active_ids: this.context.active_ids || '',
                is_visible_title: this.context.is_visible_title || '',
                pricelist_ids: this.context.selected_pricelist || default_pricelist || [],
                show_cost: this.context.show_cost,
                show_qty_on_hand: this.context.show_qty_on_hand,
            };
        },
        /**
         * Get template to display report.
         *
         * @private
         * @returns {Promise}
         */
        _getHtml: function () {
            return this._rpc({
                model: 'report.product_pricelist_matrix.report_pricelist',
                method: 'get_html',
                kwargs: {
                    data: this._prepareActionReportParams(),
                    context: this.context,
                },
            }).then(result => {
                this.reportHtml = result;
            });
        },
        /**
         * Reload report.
         *
         * @private
         * @returns {Promise}
         */
        _reload: function () {
            return this._getHtml().then(() => {
                this.$('.o_content').html(this.reportHtml);
            });
        },
        /**
         * Render search view and print button.
         *
         * @private
         */
        _renderComponent: function () {
            const $buttons = $('<button>', {
                class: 'btn btn-primary',
                text: _t("Print PDF"),
            }).on('click', this._onClickPrint.bind(this));

            var $excle_print = $('<button>', {
                class: 'btn btn-primary ml-3',
                text: _t("Print Excel"),
            }).on('click', this._onClickExcelPrint.bind(this));
            $buttons.push($excle_print[0])

            const $searchview = $(QWeb.render('product_pricelist_matrix.report_pricelist_search'));
            this.many2manytags.appendTo($searchview.find('.o_pricelist'));
            var default_pricelist = null
            if (this.context.default_pricelist) {
                default_pricelist = [this.context.default_pricelist[0]["id"]]
            }

            if (default_pricelist && Object.keys(this.context.default_pricelist).length > 0) {
                this.many2manytags._addTag(this.context.default_pricelist);
            }
            $searchview.on('click', '.o_update_options', this.on_update_options);
            return { $buttons, $searchview };
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        on_update_options: function () {
            var self = this
            if (self.many2manytags) {
                var values = [];
                for (let index = 0; index < self.many2manytags.value.res_ids.length; index++) {
                    values.push(self.many2manytags.value.res_ids[index]);
                }
                this.context.selected_pricelist = values
                this.context.show_cost  = this.$el.find("input[name='show_cost']").prop("checked")
                this.context.show_qty_on_hand  = this.$el.find("input[name='show_qty_on_hand']").prop("checked")
                this._reload()
            }
            console.log(">>>>>>>>>>>>>>", this)
        },

        /**
         * Print report in PDF when button clicked.
         *
         * @private
         */
        _onClickPrint: function () {
            return this.do_action({
                type: 'ir.actions.report',
                report_type: 'qweb-pdf',
                report_name: 'product_pricelist_matrix.report_pricelist',
                report_file: 'product_pricelist_matrix.report_pricelist',
                data: this._prepareActionReportParams(),
                print_report_name: 'ASDDDDDD'
            });
        },

        _onClickExcelPrint: function () {
            $.ajax({
                type: "POST",
                url: "/product_pricelist_matrix/excel",
                data: { data: JSON.stringify(this._prepareActionReportParams()) },
                xhrFields: {
                    responseType: 'blob'
                },
                dataType: 'binary',
                success: function (response) {
                    var link = document.createElement('a');
                    link.href = window.URL.createObjectURL(response);
                    link.download = "Pricelist_" + new Date().toDateString() + ".xlsx";
                    link.click();
                }
            });
        }

    });

    core.action_registry.add('generate_pricelist_matrix', GeneratePriceListMatrix);

    return {
        GeneratePriceListMatrix,
    };

});
