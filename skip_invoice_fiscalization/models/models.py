# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    skip_fiscalization = fields.Boolean()

    @api.depends("move_type", "skip_fiscalization")
    def set_fiscalization(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        enable_fiscalization = (ICPSudo.get_param('einvoice_register.enable_fiscalization')) or "enable"
        for rec in self:
            if enable_fiscalization == "enable":
                if rec.move_type in ["out_invoice", "out_refund"]:
                    if not rec.skip_fiscalization:
                        rec.enable_fiscalization = True
                    else:
                        rec.enable_fiscalization = False
                else:
                    rec.enable_fiscalization = False
            elif enable_fiscalization == "disable":
                rec.enable_fiscalization = False
            else:
                rec.enable_fiscalization = False



