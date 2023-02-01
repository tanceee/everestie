# -*- coding: utf-8 -*-
from odoo import fields, models


class IrModel(models.Model):
    _inherit = 'ir.model'

    disable_create_edit_model = fields.Boolean(
        string='Disable Create & Edit')
