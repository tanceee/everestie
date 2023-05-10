# -*- coding: utf-8 -*-

from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_operating_unit = fields.Boolean('Allow Operating Unit', default=True)
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")


class PosOrder(models.Model):
    _inherit = "pos.order"

    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        # print("ui_order", ui_order)
        session_id = self.env['pos.session'].sudo().browse(ui_order['pos_session_id'])
        if session_id.config_id.allow_operating_unit:
            # operating_unit_id = self.env['res.users'].sudo().browse(ui_order['user_id']).default_operating_unit_id
            operating_unit_id = session_id.config_id.operating_unit_id
            if operating_unit_id:
                res['operating_unit_id'] = operating_unit_id.id
                if res.get('lines'):
                    for line in res.get('lines'):
                        line[2]['operating_unit_id'] = operating_unit_id.id
        return res

    def _prepare_invoice_vals(self):
        res = super()._prepare_invoice_vals()
        if self.operating_unit_id:
            res.update({"operating_unit_id": self.operating_unit_id.id})
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'
    _description = 'Operating Unit'

    address = fields.Text(compute="_compute_only_address")

    def _compute_only_address(self):
        for rec in self:
            if rec.partner_id:
                rec.address = rec.partner_id._display_address(without_company=True)
            else:
                rec.address = ""
