odoo.define('os_disable_quick_create', function(require) {
    "use strict";

    var  relational_fields = require('web.relational_fields'),
         FieldMany2One = relational_fields.FieldMany2One,
         rpc = require('web.rpc'),
         model_deferred = $.Deferred(),
         models = [];
    rpc.query({
                model: 'ir.model',
                method: 'search_read',
                args: [[['disable_create_edit_model', '=', true]], ['model']],
              })
        .then(function(result) {
            result.forEach(function(el){
                models.push(el.model);
            })
            model_deferred.resolve();
        });

    FieldMany2One.include({
        init: function(parent, fieldname, record, therest) {
            this._super(parent, fieldname, record, therest);
            this.nodeOptions.no_quick_create = true;
            if (models.includes(this.field.relation)){
                this.nodeOptions.no_create_edit = true;
            }
        },
    });
});
