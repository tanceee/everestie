from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        # print("\n\n VVVVVVVVVvv", self.read())
        vals.update({'skip_fiscalization': self.skip_fiscalization})
        # print("VALSSSSSSSSSSS", vals)
        return vals

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_invoice_report = fields.Boolean("Allow Invoice Report Details")
    enable_details_invoice_report = fields.Boolean("Allow Details Of Invoice")

    @api.constrains('enable_invoice_report', 'enable_details_invoice_report')
    def _check_enable_invoice_report(self):
        for record in self:
            if record.enable_invoice_report or record.enable_details_invoice_report:
                if not record.module_account:
                    raise ValidationError("Please select Print invoices on customer request")
