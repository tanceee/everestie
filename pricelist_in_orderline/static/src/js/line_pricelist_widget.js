odoo.define('pricelist_in_orderline.LinePricelistWidget', function (require) {
    "use strict";

    var core = require('web.core');

    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var _t = core._t;

    var LinePricelistWidget = Widget.extend({
        template: 'pricelist_in_orderline.pricelist_info',
        events: _.extend({}, Widget.prototype.events, {
            'click .fa-money': '_onClickButton',
        }),

        /**
         * @override
         * @param {Widget|null} parent
         * @param {Object} params
         */
        init: function (parent, params) {
            this.data = params.data;
            this.fields = params.fields;
            this._super(parent);
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._setPopOver();
            });
        },


        updateState: function (state) {
            this.$el.popover('dispose');
            var candidate = state.data[this.getParent().currentRow];
            if (candidate) {
                this.data = candidate.data;
                this.renderElement();
                this._setPopOver();
            }
        },


        _getContent() {
            if (!this.data.price_details_html) {
                return;
            }
            var $content = this.data.price_details_html
            return $content;
        },
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        /**
         * Set a bootstrap popover on the current QtyAtDate widget that display available
         * quantity.
         */
        _setPopOver() {
            const $content = this._getContent();
            if (!$content) {
                return;
            }
            const options = {
                content: $content,
                html: true,
                placement: 'right',
                title: _t('Price Info'),
                trigger: 'focus',
                delay: { 'show': 0, 'hide': 100 },
            };
            this.$el.popover(options);
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
        _onClickButton: function () {

            // We add the property special click on the widget link.
            // This hack allows us to trigger the popover (see _setPopOver) without
            // triggering the _onRowClicked that opens the order line form view.
            this.$el.find('.fa-money').prop('special_click', true);
        },
    });

    widget_registry.add('line_pricelist_widget', LinePricelistWidget);
});
