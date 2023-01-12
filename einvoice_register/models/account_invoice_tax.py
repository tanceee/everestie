# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class AccountInvoiceTax(models.Model):
    _name = "account.invoice.tax"
    _description = "Invoice Tax"
    _order = 'sequence'

    @api.depends('invoice_id.invoice_line_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for invoice in self.mapped('invoice_id'):
            tax_grouped[invoice.id] = invoice.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'analytic_account_id': tax.analytic_account_id.id,
                    'analytic_tag_ids': tax.analytic_tag_ids.ids or False,
                })
                if tax.invoice_id and key in tax_grouped[tax.invoice_id.id]:
                    tax.base = tax_grouped[tax.invoice_id.id][key]['base']
                else:
                    _logger.warning(
                        'Tax Base Amount not computable probably due to a change in an underlying tax (%s).',
                        tax.tax_id.name)

    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True,
                                 domain=[('deprecated', '=', False)])
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    amount = fields.Monetary('Tax Amount')
    amount_rounding = fields.Monetary('Amount Delta')
    amount_total = fields.Monetary(string="Amount Total", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True,
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)

    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding


class AccountTax(models.Model):
    _inherit = "account.tax"

    def get_grouping_key(self, invoice_tax_val):
        print("self", self)
        """ Returns a string that will be used to group account.invoice.tax sharing the same properties"""
        self.ensure_one()
        return str(invoice_tax_val['tax_id'])

               # + '-' + \
               # str(invoice_tax_val['account_id']) + '-' + \
               # str(invoice_tax_val['analytic_account_id']) + '-' + \
               # str(invoice_tax_val.get('analytic_tag_ids', []))
