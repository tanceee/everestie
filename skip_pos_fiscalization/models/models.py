# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    skip_fiscalization = fields.Boolean()

    def fiscalize(self):
        if not self.config_id.disable_fiscalization and not self.skip_fiscalization:
            super().fiscalize()
        if self.skip_fiscalization:
            self.fiscalization_tries = 5

    @api.model
    def _order_fields(self, ui_order):
        fields = super(PosOrder, self)._order_fields(ui_order)
        fields["skip_fiscalization"] = ui_order.get('skip_fiscalization')
        return fields
