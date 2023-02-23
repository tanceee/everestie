# -*- coding: utf-8 -*-
from odoo import api, models
from datetime import datetime

class SaleTaxInvioiceReport110(models.AbstractModel):
    _name = 'report.pways_invoice_report.main_sale_tax_invoice110'
    _description = 'Report Invoice'

    @api.model
    def get_date(self, invoice):
        date = ''
        if invoice.invoice_date:
            date = datetime.strptime(str(invoice.invoice_date),"%Y-%m-%d").strftime('%d/%m/%Y')
        return date

    @api.model
    def get_amounts(self, invoice_line):
        taxable_without_discount = 0.0
        unit_price = invoice_line.price_unit
        if invoice_line.tax_ids:
            if invoice_line.tax_ids.price_include:
                tax_from_price = invoice_line.price_unit * invoice_line.tax_ids.amount / 100
                unit_price = invoice_line.price_unit /  ( 1+ invoice_line.tax_ids.amount / 100 )
                
        taxable_without_discount = unit_price * invoice_line.quantity
        taxable_amount = taxable_without_discount
        if invoice_line.discount:
            discount_amount = taxable_amount * invoice_line.discount / 100
            taxable_amount = taxable_amount - discount_amount
        tax_amount = taxable_amount * invoice_line.tax_ids.amount / 100
        final_total = taxable_amount + tax_amount

        return unit_price, \
               taxable_without_discount, \
               taxable_amount, \
               tax_amount, \
               final_total

    @api.model
    def get_discount(self, invoice_line):
        if not invoice_line.discount:
            return ''
        else:
            return str(invoice_line.discount) + "%"

    @api.model
    def get_rate_info(self, invoice):
        company_currency = invoice.company_id and \
                           invoice.company_id.currency_id and \
                           invoice.company_id.currency_id.name or ''
        invoice_currency = \
            invoice.currency_id and invoice.currency_id.name or ''
        currency_rate = invoice.currency_rate
        rate_info = "1 " + str(invoice_currency) + " = " + str(currency_rate)\
                    + " " + str(company_currency)
        return rate_info

    @api.model
    def get_base_currency_total(self, amount, invoice):
        total = amount
        if invoice.company_id.currency_id != invoice.currency_id and total > 0:
            total = (amount) / (1 / invoice.currency_rate)
        return round(total, 2)

    def get_invoiced_lot_values(self, move):
        return move._get_invoiced_lot_values()

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env['account.move'].browse(docids[0])
        return {
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'get_date': self.get_date,
            'get_amounts': self.get_amounts,
            'get_rate_info': self.get_rate_info,
            'get_base_currency_total': self.get_base_currency_total,
            'get_discount': self.get_discount,
            'get_invoiced_lot_values': self.get_invoiced_lot_values
        }

class SaleTaxInvioiceReportDetails(models.AbstractModel):
    _name = 'report.pways_invoice_report.main_sale_tax_invoice_details'
    _description = 'Report Invoice Details'

    @api.model
    def get_date(self, invoice):
        date = ''
        if invoice.invoice_date:
            date = datetime.strptime(str(invoice.invoice_date),"%Y-%m-%d").strftime('%d/%m/%Y')
        return date

    def get_invoiced_lot_values(self, move):
        return move._get_invoiced_lot_values()

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env['account.move'].browse(docids[0])
        return {
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'get_date': self.get_date,
            'get_invoiced_lot_values': self.get_invoiced_lot_values
        }


