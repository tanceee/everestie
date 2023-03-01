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
<<<<<<< HEAD
=======
from odoo.exceptions import UserError
>>>>>>> 00746b09d640d62892b25aefd7d845975ca8a505
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

    def _move_autocomplete_invoice_lines_values(self):
        self.ensure_one()
        return super(account_move,
                     self.with_context(currency_rate=self.currency_rate))._move_autocomplete_invoice_lines_values()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('currency_id')
    def _onchange_currency(self):
        for line in self:
            print("LINE--------------", line.move_id.currency_rate)
            company = line.move_id.company_id

            if line.move_id.is_invoice(include_receipts=True):
                print("wwwwwwwwwww")
                if line.move_id.currency_rate:
                    line.with_context(currency_rate=line.move_id.currency_rate)._onchange_price_subtotal()
                else:
                    line._onchange_price_subtotal()

            elif not line.move_id.reversed_entry_id:
                if line.move_id.currency_rate:
                    print("dddddddddddddddddddddd")
                    balance = line.currency_id.with_context(currency_rate=line.move_id.currency_rate)._convert(
                        line.amount_currency, company.currency_id, company,
                        line.move_id.date or fields.Date.context_today(line))
                else:
                    balance = line.currency_id._convert(line.amount_currency, company.currency_id, company,
                                                        line.move_id.date or fields.Date.context_today(line))

                line.debit = balance if balance > 0.0 else 0.0
                line.credit = -balance if balance < 0.0 else 0.0


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
<<<<<<< HEAD
            invoice_vals.update(currency_rate=1 / self.currency_rate)
=======
            invoice_vals.update(currency_rate=self.currency_id.inverse_rate)
>>>>>>> 00746b09d640d62892b25aefd7d845975ca8a505
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

<<<<<<< HEAD
=======

class AccountPayment(models.Model):
    _inherit = "account.payment"

    inverse_currency_rate = fields.Float('Inverse Rate', digits=0)
    is_same_currency = fields.Boolean('Same Currency')

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0
        if not self.is_same_currency:
            write_off_balance = self.currency_id.with_context(currency_rate=self.inverse_currency_rate)._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id.with_context(currency_rate=self.inverse_currency_rate)._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        else:
            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else:  # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = self._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if not self.currency_id.is_zero(write_off_amount_currency):
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list


class AccountPaymentReg(models.TransientModel):
    _inherit = "account.payment.register"

    inverse_currency_rate = fields.Float('Inverse Rate', digits=0)
    is_same_currency = fields.Boolean('Same Currency', compute="compute_currency_same")

    @api.depends("currency_id")
    def compute_currency_same(self):
        print("self._context", self._context)
        for rec in self:
            if rec.currency_id.id == rec.company_currency_id.id:
                rec.is_same_currency = True
            else:
                rec.is_same_currency = False

    @api.onchange("currency_id")
    def set_rate(self):
        if not self.is_same_currency:
            invoice_id = self._context.get("active_id")
            if invoice_id:
                invoice_id = self.env["account.move"].browse(invoice_id)
                self.inverse_currency_rate = invoice_id.currency_id.inverse_rate

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentReg, self)._create_payment_vals_from_wizard()
        payment_vals.update(
            {"inverse_currency_rate": self.inverse_currency_rate, "currency_rate": self.inverse_currency_rate,
             "is_same_currency": self.is_same_currency})
        return payment_vals

    # def _post_payments(self, to_process, edit_mode=False):
    #     """ Post the newly created payments.
    #
    #     :param to_process:  A list of python dictionary, one for each payment to create, containing:
    #                         * create_vals:  The values used for the 'create' method.
    #                         * to_reconcile: The journal items to perform the reconciliation.
    #                         * batch:        A python dict containing everything you want about the source journal items
    #                                         to which a payment will be created (see '_get_batches').
    #     :param edit_mode:   Is the wizard in edition mode.
    #     """
    #     payments = self.env['account.payment']
    #     for vals in to_process:
    #         payment = vals['payment']
    #         if not payment.is_same_currency and payment.inverse_currency_rate:
    #             print(" payment.inverse_currency_rate",  payment.inverse_currency_rate)
    #             payment.move_id.currency_rate = payment.inverse_currency_rate
    #             payment.move_id.onchange_currency_rate()
    #         payments |= vals['payment']
    #     payments.action_post()

    # @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id',
    #              'payment_date')
    # def _compute_amount(self):
    #     for wizard in self:
    #         if wizard.source_currency_id == wizard.currency_id:
    #             # Same currency.
    #             wizard.amount = wizard.source_amount_currency
    #         elif wizard.currency_id == wizard.company_id.currency_id:
    #             # Payment expressed on the company's currency.
    #             wizard.amount = wizard.source_amount
    #         else:
    #             # Foreign currency on payment different than the one set on the journal entries.
    #             amount_payment_currency = wizard.company_id.currency_id.with_context(
    #                 currency_rate=1 / self.inverse_currency_rate)._convert(wizard.source_amount,
    #                                                                        wizard.currency_id, wizard.company_id,
    #                                                                        wizard.payment_date or fields.Date.today())
    #             wizard.amount = amount_payment_currency
    #
    # @api.depends('amount')
    # def _compute_payment_difference(self):
    #     for wizard in self:
    #         if wizard.source_currency_id == wizard.currency_id:
    #             # Same currency.
    #             wizard.payment_difference = wizard.source_amount_currency - wizard.amount
    #         elif wizard.currency_id == wizard.company_id.currency_id:
    #             # Payment expressed on the company's currency.
    #             wizard.payment_difference = wizard.source_amount - wizard.amount
    #         else:
    #             # Foreign currency on payment different than the one set on the journal entries.
    #             amount_payment_currency = wizard.company_id.currency_id.with_context(
    #                 currency_rate=1 / self.inverse_currency_rate)._convert(wizard.source_amount,
    #                                                                        wizard.currency_id, wizard.company_id,
    #                                                                        wizard.payment_date or fields.Date.today())
    #             wizard.payment_difference = amount_payment_currency - wizard.amount

>>>>>>> 00746b09d640d62892b25aefd7d845975ca8a505
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
