# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, tools, _
from odoo.tools import float_round


class account_move(models.Model):
    _inherit = 'account.move'

    currency_rate = fields.Float('Inverse Rate', digits=0, readonly=True, states={'draft': [('readonly', False)]})
    is_same_currency = fields.Boolean('Same Currency')

    @api.onchange('currency_id')
    def onchange_currency_id_rate(self):
        if self.currency_id:
            if self.currency_id.id == self.company_id.currency_id.id:
                self.is_same_currency = True
            else:
                self.is_same_currency = False

            currency_rate = self.currency_id.with_context(dict(self._context or {}, date=self.invoice_date)).rate
            if currency_rate:
                self.currency_rate = 1 / currency_rate
            self.with_context(currency_rate=self.currency_rate)._onchange_currency()

    @api.onchange('currency_rate', "invoice_line_ids")
    def onchange_currency_rate(self):
        if self.currency_rate:
            self.with_context(currency_rate=self.currency_rate)._onchange_currency()


class res_currency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        res = super(res_currency, self)._get_conversion_rate(from_currency, to_currency, company, date)
        if self._context.get('currency_rate'):
            return self._context.get('currency_rate')
        return res

    def _convert(self, from_amount, to_currency, company, date, round=True):
        res = super(res_currency, self)._convert(from_amount, to_currency, company, date, round)
        self, to_currency = self or to_currency, to_currency or self
        if self._context.get('currency_rate') and self != to_currency:
            # if self._context.get('currency_rate'):
            #     to_amount = from_amount / self._get_conversion_rate(self, to_currency, company, date)
            # else:
            to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
            aa_amount = to_currency.round(to_amount) if round else to_amount
            return aa_amount
        return res


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        if invoice_vals and order.currency_rate:
            invoice_vals.update(currency_rate=1 / order.currency_rate)
        return invoice_vals


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if invoice_vals and self.currency_rate:
            invoice_vals.update(currency_rate=1 / self.currency_rate)
        return invoice_vals


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    currency_rate_inverse = fields.Float("Currency Rate Inverse", digits=0)
    is_same_currency = fields.Boolean('Same Currency')

    @api.onchange("currency_id")
    def set_currency_rate_inverse(self):
        currency_rate = self.env['res.currency']._get_conversion_rate(self.company_id.currency_id,
                                                                      self.currency_id, self.company_id,
                                                                      self.date_order)
        if currency_rate:
            self.currency_rate_inverse = 1 / currency_rate

        if self.currency_id.id == self.company_id.currency_id.id:
            self.is_same_currency = True
        else:
            self.is_same_currency = False

    @api.depends('date_order', 'currency_id', 'company_id', 'company_id.currency_id', 'currency_rate_inverse')
    def _compute_currency_rate(self):
        for order in self:
            if order.currency_rate_inverse:
                order.currency_rate = 1 / order.currency_rate_inverse
            else:
                order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id,
                                                                                    order.currency_id, order.company_id,
                                                                                    order.date_order)

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        if invoice_vals and self.currency_rate:
            invoice_vals.update(currency_rate=1 / self.currency_rate)
        return invoice_vals

    def action_view_invoice(self, invoices=False):
        invoice_action = super(PurchaseOrder, self).action_view_invoice(invoices)
        if invoices:
            for inv in invoices:
                if inv.currency_rate:
                    # inv.with_context(currency_rate=inv.currency_rate)._onchange_currency()
                    if inv.is_invoice(include_receipts=True):
                        for line in inv._get_lines_onchange_currency():
                            # line.currency_id = currency
                            line.with_context(currency_rate=inv.currency_rate,
                                              check_move_validity=False)._onchange_currency()
                    else:
                        for line in inv.line_ids:
                            line.with_context(currency_rate=inv.currency_rate,
                                              check_move_validity=False)._onchange_currency()

                    inv._recompute_dynamic_lines(recompute_tax_base_amount=True)
        return invoice_action

    def _prepare_supplier_info(self, partner, line, price, currency):
        values = super(PurchaseOrder, self)._prepare_supplier_info(partner, line, price, currency)
        if values:
            if not self.is_same_currency:
                price = self.currency_id.with_context(currency_rate=self.currency_rate_inverse)._convert(
                    line.price_unit, currency, line.company_id,
                    line.date_order or fields.Date.today(), round=False)
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)
                values.update(price=price)
        return values


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                   cost):
        account_move_vals = super(StockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id,
                                                                              journal_id, qty, description, svl_id,
                                                                              cost)
        if account_move_vals and self.purchase_line_id:
            currency_rate_inverse = self.purchase_line_id.order_id.currency_rate_inverse
            account_move_vals.update(currency_rate=currency_rate_inverse)
        return account_move_vals

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = \
                    line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id,
                                                                        quantity=qty)['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                price_unit = order.currency_id.with_context(currency_rate=order.currency_rate_inverse)._convert(
                    price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self),
                    round=False)
                # print("price_unit", price_unit)
            return price_unit
        return super(StockMove, self)._get_price_unit()

# class StockValuationLayer(models.Model):
#     """Stock Valuation Layer"""
#
#     _inherit = 'stock.valuation.layer'
#
#     def _validate_accounting_entries(self):
#         am_vals = []
#         for svl in self:
#             if not svl.product_id.valuation == 'real_time':
#                 continue
#             if svl.currency_id.is_zero(svl.value):
#                 continue
#             am_vals += svl.stock_move_id._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
#         if am_vals:
#             account_moves = self.env['account.move'].sudo().create(am_vals)
#             for account__move in account_moves:
#                 if account__move.currency_rate:
#                     inv = account__move
#                     if inv.is_invoice(include_receipts=True):
#                         for line in inv._get_lines_onchange_currency():
#                             # line.currency_id = currency
#                             line.with_context(currency_rate=inv.currency_rate,
#                                               check_move_validity=False)._onchange_currency()
#                     else:
#                         for line in inv.line_ids:
#                             line.with_context(currency_rate=inv.currency_rate,
#                                               check_move_validity=False)._onchange_currency()
#
#                     inv._recompute_dynamic_lines(recompute_tax_base_amount=True)
#
#             account_moves._post()
#         for svl in self:
#             # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
#             if svl.company_id.anglo_saxon_accounting:
#                 svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(
#                     product=svl.product_id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
