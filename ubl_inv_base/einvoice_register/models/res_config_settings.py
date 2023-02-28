# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_fiscalization = fields.Selection([("enable", "Enable"), ("disable", "Disable")], "Fisclization (E-Invoice)",
                                            default="enable")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('einvoice_register.enable_fiscalization', self.enable_fiscalization)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        enable_fiscalization = (ICPSudo.get_param('einvoice_register.enable_fiscalization')) or "enable"

        res.update(
            enable_fiscalization=enable_fiscalization,
        )
        return res
