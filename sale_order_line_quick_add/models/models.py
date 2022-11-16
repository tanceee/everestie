# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_quick_add(self):
        wizard_id = self.env["quick.order.wizard"].create({"created": True, "order_id": self.id})
        return {
            'name': _('Order Lines Quick Add'),
            'view_mode': 'form',
            'res_model': 'quick.order.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wizard_id.id,
        }
