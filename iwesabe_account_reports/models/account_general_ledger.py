# * coding: utf8 *


from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from datetime import timedelta
from odoo.tools import float_is_zero


class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"

    filter_salesperson = True

    @api.model
    def _get_options_domain(self, options):
        domain = super(report_account_general_ledger,
                       self)._get_options_domain(options)
        if options.get('salesperson') and options.get('salespersons'):
            salespersons = [int(salesperson) for salesperson in options['salespersons']]
            domain.append(('invoice_user_id', 'in', salespersons))
        return domain
