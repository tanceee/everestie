# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.account.wizard.pos_box import CashBox as PoSCashBox
from odoo.exceptions import UserError


def _create_bank_statement_line(self, record):
    partner = self.env.context.get('partner_id', False)
    print("partner============================", partner)
    for box in self:
        if record.state == 'confirm':
            raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
        values = box._calculate_values_for_statement_line(record)
        if partner:
            partner_id = self.env['res.partner'].browse(int(partner))
            if partner_id:
                values.update({
                    'partner_id': partner_id.id,
                })
        self.env['account.bank.statement.line'].sudo().create(values)

PoSCashBox._create_bank_statement_line = _create_bank_statement_line