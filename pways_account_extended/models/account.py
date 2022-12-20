# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import fields, models
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoiced_lot_values(self):
        lot_values = super(AccountMove, self)._get_invoiced_lot_values()
        if self.state == 'draft':
            return lot_values
        lot_values = []
        # user may not have access to POS orders, but it's ok if they have
        # access to the invoice
        for order in self.sudo().pos_order_ids:
            for line in order.lines:
                lots = line.pack_lot_ids or False
                for lot in lots:
                    lot_id = self.env['stock.production.lot'].search([('name', '=', lot.lot_name), ('product_id', '=', lot.product_id.id)], limit=1)
                    lot_values.append({
                        'product_name': lot.product_id.name,
                        'quantity': line.qty if lot.product_id.tracking == 'lot' else 1.0,
                        'uom_name': line.product_uom_id.name,
                        'lot_name': lot.lot_name,
                        'expiry_date': lot_id and lot_id.expiration_date.strftime('%d/%m/%Y')
                    })

        return lot_values