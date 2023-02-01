# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class PoSSession(models.Model):
    _inherit = 'pos.session'

    def try_cash_in_out(self, _type, amount, reason, extras):
        sign = 1 if _type == 'in' else -1
        self.env['cash.box.out']\
            .with_context({'active_model': 'pos.session', 'active_ids': self.ids, 'partner_id': extras['partner_id']})\
            .create({'amount': sign * amount, 'name': reason})\
            .run()
        message_content = [f"Cash {extras['translatedType']}", f'- Amount: {extras["formattedAmount"]}']
        if reason:
            message_content.append(f'- Reason: {reason}')
        self.message_post(body='<br/>\n'.join(message_content))