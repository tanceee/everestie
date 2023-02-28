odoo.define('einvoice_register.ActionManager', function (require) {
    "use strict";
    var ActionManager = require('web.ActionManager');
    var config = require('web.config');
    var framework = require('web.framework');

    ActionManager.include({
        _executeURLAction: function (action, options) {
            var url = action.url;
            if (config.debug && url && url.length && url[0] === '/') {
                url = $.param.querystring(url, { debug: config.debug });
            }
            if (action.target === 'download') {
                framework.redirect(url);
                return $.when();
            }
            else{
                return this._super(action, options);
            }
        },
    });
});

