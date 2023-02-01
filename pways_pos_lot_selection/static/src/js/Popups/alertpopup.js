odoo.define('point_of_sale.PwaysAlertPopUp', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class PwaysAlertPopUp extends AbstractAwaitablePopup {
        getPayload() {
            return null;
        }
    }
    PwaysAlertPopUp.template = 'PwaysAlertPopUp';
    PwaysAlertPopUp.defaultProps = {
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(PwaysAlertPopUp);
    return PwaysAlertPopUp;
});
