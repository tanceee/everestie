# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, tools,_

class account_move(models.Model):   
    _inherit = 'account.move'
    
    currency_rate = fields.Float('Rate',digits=(12, 6),readonly=True,states={'draft': [('readonly', False)]})
    is_same_currency = fields.Boolean('Same Currency')
    
    @api.onchange('currency_id')
    def onchange_currency_id_rate(self):
        if self.currency_id:
            if self.currency_id.id == self.company_id.currency_id.id:
                self.is_same_currency = True
            else:
                self.is_same_currency = False
                
            self.currency_rate = self.currency_id.with_context(dict(self._context or {}, date=self.invoice_date)).inverse_rate
            self.with_context(currency_rate=self.currency_rate)._onchange_currency()
    
    @api.onchange('currency_rate')
    def onchange_currency_rate(self):
        if self.currency_rate:
            self.with_context(currency_rate=self.currency_rate)._onchange_currency()


class res_currency(models.Model):
    _inherit = 'res.currency'
    
    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        res = super(res_currency,self)._get_conversion_rate(from_currency, to_currency, company, date)
        if self._context.get('currency_rate'):
            return self._context.get('currency_rate')
        return res
        
    
    def _convert(self, from_amount, to_currency, company, date, round=True):
        res  = super(res_currency,self)._convert(from_amount, to_currency, company, date, round)
        self, to_currency = self or to_currency, to_currency or self
        if self._context.get('currency_rate') and self != to_currency:
            if self._context.get('currency_rate'):
                to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
            else:
                to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
            aa_amount = to_currency.round(to_amount) if round else to_amount
            return aa_amount
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    
