import base64
import re
import uuid
from datetime import datetime
from io import BytesIO
import logging

import qrcode
import requests
from dateutil import tz
from lxml import etree
# from ..services.http_calls.request import make_http_call
from odoo.addons.fiscalization_base.services.http_calls.request import make_http_call
# from ..services.utils import iic
from odoo.addons.fiscalization_base.services.utils import iic

from odoo import api, fields, models, _
from odoo import http
from odoo.addons.base.models.ir_sequence import _predict_nextval
from odoo.exceptions import ValidationError, UserError
from odoo.http import request, content_disposition
from odoo.tools import float_is_zero, float_round
from . import e_invoice
from . import fetch_e_invoice
from ..services.invoice import make_invoice

from_zone = tz.gettz('UTC')
to_zone = tz.gettz('Europe/Tirane')
ACCEPTABLE_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg", "text/csv",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         "application/vnd.oasis.opendocument.spreadsheet"]

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'base.ubl']

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        result = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)
        result.update({'business_process': "P9", "type_code": "384"})
        return result

    @api.model
    def default_get(self, default_fields):
        res = super(AccountInvoice, self).default_get(default_fields)
        if 'move_type' in res:
            if res['move_type'] == 'out_refund':
                res['business_process'] = 'P9'
                res['type_code'] = '384'

            elif res['move_type'] == 'out_invoice':
                res['business_process'] = 'P1'
        return res

    @api.onchange("fiscal_position_id")
    def update_inv_type(self):
        if self.fiscal_position_id:
            self.type_of_self_iss = False
            if self.fiscal_position_id.for_export:
                self.is_export = True
            else:
                self.is_export = False
            if self.fiscal_position_id.for_self_inv:
                self.is_self_inv = True
            else:
                self.is_self_inv = False
            if self.fiscal_position_id.for_reverse_charge:
                self.is_reverse_charge = True
                self.type_of_self_iss = "ABROAD"
            else:
                self.is_reverse_charge = False
        else:
            self.is_export = False
            self.is_self_inv = False
            self.is_reverse_charge = False
            self.type_of_self_iss = False

    @api.depends("move_type")
    def set_fiscalization(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        enable_fiscalization = (ICPSudo.get_param('einvoice_register.enable_fiscalization')) or "enable"
        print("enable_fiscalization", enable_fiscalization)
        for rec in self:
            if enable_fiscalization == "enable":
                if rec.move_type in ["out_invoice", "out_refund"]:
                    rec.enable_fiscalization = True
                else:
                    rec.enable_fiscalization = False
            elif enable_fiscalization == "disable":
                rec.enable_fiscalization = False
            else:
                rec.enable_fiscalization = False

    enable_fiscalization = fields.Boolean("Fisclization (E-Invoice)", compute="set_fiscalization", store=True)
    output = fields.Binary(readonly=True)
    file_name = fields.Char()
    header_UUID = fields.Char(string="Header UUID", readonly=True, copy=False)
    header_send_datetime = fields.Char("Header Date Time", readonly=True, copy=False)
    header_subseq_delivery_type = fields.Selection(selection=[('NOINTERNET', 'NOINTERNET'),
                                                              ('BOUNDBOOK', 'BOUNDBOOK'),
                                                              ('SERVICE', 'SERVICE'),
                                                              ('TECHNICALERROR', 'TECHNICALERROR')], default='SERVICE')

    # Invoice Period

    start_date = fields.Date()
    end_date = fields.Date()

    # INVOICE
    type_of_invoice = fields.Selection(selection=[('CASH', 'CASH'), ('NONCASH', 'NONCASH')], default='NONCASH')
    is_self_inv = fields.Boolean()
    type_of_self_iss = fields.Selection(
        selection=[('AGREEMENT', '[AGREEMENT] The previous agreement between the parties'),
                   ('DOMESTIC', '[DOMESTIC] Purchase from domestic farmers'),
                   ('ABROAD', '[ABROAD] Purchase of services from abroad'),
                   ('SELF', '[SELF] Self-consumption'),
                   ('OTHER', '[OTHER] Other')], default=None)
    business_process = fields.Selection(
        [('P1', '[P1] Invoicing the supply of goods and services ordered on a contract basis'),
         ('P2', '[P2] Periodic invoicing of contract-based delivery'),
         ('P3', '[P3] Invoicing delivery over unforeseen orders'),
         ('P4', '[P4] Advance Payment'),
         ('P5', '[P5] Spot payment'),
         ('P6', '[P6] Payment before delivery on the based on a purchase order'),
         ('P7', '[P7] Invoices with reference to a dispatch note'),
         ('P8', '[P8] Invoices with reference to dispatch and receipt'),
         ('P9', '[P9] Approval or Negative Invoicing'),
         ('P10', '[P10] Corrective Invoicing'),
         ('P11', '[P11] Partial and final invoicing'),
         ], default="P1", required=True, )

    type_code = fields.Selection([("80", "[80] Debit note related to goods or services"),
                                  ("82", "[82] Metered services invoice"),
                                  ("84", "[84] Debit note related to financial adjustments"),
                                  ("380", "[380] Commercial invoice"),
                                  ("383", "[383] Debit note"),
                                  ("384", "[384] Corrective invoice"),
                                  ("386", "[386] Prepayment invoice"),
                                  ("388", "[388] Tax invoice"),
                                  ("393", "[393] Factored invoice"),
                                  ("395", "[395] Consignment invoice"),
                                  ("575", "[575] Forwarder's invoice"),
                                  ("780", "[780] Freight invoice"),
                                  ("81", "[81] Credit note related to goods or services"),
                                  ("83", "[83] Credit note related to financial adjustments"),
                                  ("381", "[381] Credit note"),
                                  ("396", "[396] Factored credit note"),
                                  ("532", "[532] Forwarder's credit note"),
                                  ], default="388")

    is_simplified_invoice = fields.Selection(string="Is simplified invoice?",
                                             selection=[('true', 'true'), ('false', 'false')],
                                             default='false')
    invoice_datetime = fields.Char("Invoice Issue Date Time")
    invoice_number = fields.Char("Invoice Order Number", copy=False)
    invoice_order_number = fields.Char("Order Number", copy=False)
    invoice_tax_free_amount = fields.Float(digits=(12, 2))
    invoice_markup_amount = fields.Float(digits=(12, 2))  # optional
    invoice_goods_exported_amount = fields.Float(digits=(12, 2))  # optional
    invoice_total_amount_without_vat = fields.Float(digits=(12, 2))  # compute
    invoice_total_amount = fields.Float(digits=(12, 2))
    invoice_total_price = fields.Float(digits=(12, 2))
    invoice_import_custom_declare_number = fields.Char("Numri i deklarates doganore te importit", size=50)
    iic_code = fields.Char("IIC", size=32, copy=False)
    iic_signature = fields.Char("IIC Signature", size=512, copy=False)
    is_reverse_charge = fields.Boolean("Is Reverse Charge?")
    # CORRECTIVE INVOICE
    is_corrective_invoice = fields.Selection(string='Is corrective invoice?',
                                             selection=[('true', 'true'), ('false', 'false')],
                                             default='false')
    invoice_corrective_iic_ref = fields.Char('Kodi Identifikues i fatures qe po korigjohet', size=32, required=False)
    invoice_corrective_issue_date_time = fields.Char('Creation date and time of the invoice that is being corrected',
                                                     required=False)
    invoice_corrective_type = fields.Selection(selection=[('CORRECTIVE', 'CORRECTIVE'),
                                                          ('DEBIT', 'DEBIT'),
                                                          ('CREDIT', 'CREDIT')], default='CORRECTIVE', required=False)

    # BAD DEBT INVOICE

    is_bad_debt_invoice = fields.Boolean("Is Bad Debt Invoice?")

    # INVOICE PAY METHODS

    pay_method_type = fields.Selection(selection=[('ACCOUNT', '[ACCOUNT] Transaction account'),
                                                  ('FACTORING', '[FACTORING] Factoring'),
                                                  ('COMPENSATION', '[COMPENSATION] Compensation'),
                                                  ('TRANSFER', '[TRANSFER] Transfer of rights or debts'),
                                                  ('WAIVER', '[WAIVER] Waiver of debts'),
                                                  ('KIND', '[KIND] Payment in kind (clearing)'),
                                                  ('OTHER', '[OTHER] Other cashless payments')], default='ACCOUNT')
    pay_method_amount = fields.Float(digits=(12, 2))

    # INVOICE CURRENCY

    invoice_currency_code = fields.Char(related='currency_id.name')
    # invoice_currency_exchange_rate = fields.Float(digits=(12, 3))  # related='pricelist_id.currency_id.inverse_rate'
    invoice_currency_is_buying = fields.Selection(selection=[('true', 'true'), ('false', 'false')], default='false')

    # INVOICE SELLER

    invoice_seller_id_number = fields.Char(related='company_id.vat', size=20)
    invoice_seller_id_type = fields.Selection(selection=[('NUIS', 'NUIS'),
                                                         ('ID', 'ID'),
                                                         ('PASS', 'PASS'),
                                                         ('VAT', 'VAT'),
                                                         ('TAX', 'TAX'),
                                                         ('SOC', 'SOC')], default='NUIS')
    invoice_seller_id_name = fields.Char(related='company_id.name', size=100)
    invoice_seller_id_address = fields.Char(related='company_id.street', size=200)
    invoice_seller_id_city = fields.Char(related='company_id.city', size=100)
    invoice_seller_id_country = fields.Char(related='company_id.country_id.code')

    # INVOICE BUYER

    invoice_buyer_id_number = fields.Char(related='partner_id.vat', size=20)
    invoice_buyer_id_type = fields.Selection(selection=[('NUIS', '[NUIS] NUIS number'),
                                                        ('ID', '[ID] Personal ID number'),
                                                        ('PASS', '[PASS] Passport number'),
                                                        ('VAT', '[VAT] VAT number'),
                                                        ('TAX', '[TAX] TAX number'),
                                                        ('SOC', '[SOC] Social security number')],
                                             related='partner_id.vat_type')
    invoice_buyer_id_name = fields.Char(related='partner_id.name', size=100)
    invoice_buyer_id_address = fields.Char(related='partner_id.street', size=200)
    invoice_buyer_id_city = fields.Char(related='partner_id.city', size=100)
    invoice_buyer_id_country = fields.Char(related='partner_id.country_id.code')

    # INVOICE SAME TAXES

    invoice_same_tax_number_of_items = fields.Integer()  # to be computed
    invoice_same_tax_price_before_vat = fields.Float(digits=(12, 2))
    invoice_same_tax_vat_rate = fields.Float(digits=(12, 2))
    invoice_same_tax_type_of_exempt_from_vat = fields.Selection(selection=[('TYPE_1', 'TYPE_1'),
                                                                           ('TYPE_2', 'TYPE_2')],
                                                                default='TYPE_1')
    invoice_same_tax_vat_amount = fields.Float(digits=(12, 2))

    xml = fields.Char(help='Generated XML for the fiscalization process')
    fic_number = fields.Char('FIC Number', copy=False)
    eic_number = fields.Char('EIC Number', copy=False)
    is_fiscalized = fields.Boolean(copy=False)
    fiscalization_response = fields.Text(copy=False)
    is_export = fields.Boolean()
    vat_type = fields.Selection(selection=[('NUIS', '[NUIS] NUIS number'),
                                           ('ID', '[ID] Personal ID number'),
                                           ('PASS', '[PASS] Passport number'),
                                           ('VAT', '[VAT] VAT number'),
                                           ('TAX', '[TAX] TAX number'),
                                           ('SOC', '[SOC] Social security number')], related="partner_id.vat_type")

    attach_doc_ids = fields.Many2many("ir.attachment", "einvoice_doc_attach_rel", "e_invoice_id", "attachment_id")
    attach_doc_link_ids = fields.One2many("attach.doc.link", "invoice_id")
    partner_additional_bank_ids = fields.Many2many("res.partner.bank")
    tax_line_ids = fields.One2many('account.invoice.tax', 'invoice_id', string='Tax Lines',
                                   readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    transporter_id = fields.Many2one("res.partner")
    license_plate_no = fields.Char()
    delivery_datetime = fields.Datetime()

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids_2(self):
        taxes_grouped = self.get_taxes_values()
        print("taxes_grouped", taxes_grouped)
        tax_lines = self.tax_line_ids.filtered('manual')
        print("tax_lines", tax_lines)
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines
        return

    @api.onchange("transporter_id")
    def onchange_transporter(self):
        if self.transporter_id and self.transporter_id.license_plate_no:
            self.license_plate_no = self.transporter_id.license_plate_no

    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id or line.display_type:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = \
                line.tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)[
                    'taxes']
            for tax in taxes:
                print("TAX", tax)
                val = self._prepare_tax_line_vals(line, tax)
                if isinstance(tax['id'], int):
                    tax_id = tax['id']
                else:
                    tax_id = tax['id'].origin
                key = self.env['account.tax'].browse(tax_id).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped

    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        if isinstance(tax['id'], int):
            tax_id = tax['id']
        else:
            tax_id = tax['id'].origin
        vals = {
            'invoice_id': self.id,
            'name': tax['name'],
            'tax_id': tax_id,
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
            'account_id': self.move_type in ('out_invoice', 'in_invoice') and (
                    tax['account_id'] or line.account_id.id) or line.account_id.id,
            'analytic_tag_ids': tax['analytic'] and line.analytic_tag_ids.ids or False,
        }

        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
        if not vals.get('analytic_account_id') and line.analytic_account_id and vals[
            'account_id'] == line.account_id.id:
            vals['analytic_account_id'] = line.analytic_account_id.id
        return vals

    # @api.constrains('partner_id', 'partner_bank_id')
    # def validate_partner_additional_bank_ids(self):
    #     for record in self:
    #         if record.partner_additional_bank_ids:
    #             for partner_bank_id in record.partner_additional_bank_ids:
    #                 if record.move_type in ('in_invoice',
    #                                         'out_refund') and partner_bank_id.partner_id != record.partner_id.commercial_partner_id:
    #                     raise ValidationError(_("Commercial partner and vendor account owners must be identical."))
    #                 elif record.move_type in ('out_invoice',
    #                                           'in_refund') and record.company_id not in partner_bank_id.partner_id.ref_company_ids:
    #                     raise ValidationError(
    #                         _("The account selected for payment does not belong to the same company as this invoice."))

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_additional_banks(self):
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_company(company_id)
        print("P", p)
        move_type = self.move_type or self.env.context.get('move_type', 'out_invoice')

        if p:
            if move_type in ('in_invoice', 'out_refund'):
                bank_ids = p.commercial_partner_id.bank_ids
                domain = {'partner_additional_bank_ids': [('id', 'in', bank_ids.ids)]}
            elif move_type == 'out_invoice':
                domain = {'partner_additional_bank_ids': [('partner_id.ref_company_ids', 'in', [self.company_id.id])]}
                print("domain", domain)

            res = {}
            if domain:
                res['domain'] = domain
            return res

    @api.onchange("attach_doc_ids")
    def onchange_attachment(self):
        for rec in self.attach_doc_ids:
            if rec.mimetype not in ACCEPTABLE_MIME_TYPES:
                # self.attach_doc_ids = (2, rec.id, 0)
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        "Invalid file format, MIME type %s is not acceptable!\n only accept %s \n\nRemove the last file." % (
                            rec.mimetype, ACCEPTABLE_MIME_TYPES)),
                }
                return {'warning': warning}
                # raise ValidationError(
                #     "Invalid file format, MIME type %s is not acceptable!\n only accept %s " % (
                #         rec.mimetype, ACCEPTABLE_MIME_TYPES))

    # payment_mode_id = fields.Many2one(
    #     comodel_name='account.payment.mode', string="Payment Mode",
    #     ondelete='restrict',
    #     readonly=True, states={'draft': [('readonly', False)]})

    # def check_num(self):
    #     print(self.get_portal_url())
    #     seq_obj = self.env['ir.sequence'].search([('name', '=', 'INV Sequence')])
    #     print("seq_obj", seq_obj.number_next_actual) 6000 + 1000 + 5000 + 10000
    #
    @api.model
    def create(self, vals):
        rec = super(AccountInvoice, self).create(vals)
        # TODO set the dates from main invoice in credit note
        if rec.reversed_entry_id:
            rec.start_date = rec.reversed_entry_id.start_date
            rec.end_date = rec.reversed_entry_id.end_date
        return rec

    # @api.onchange("is_bad_debt_invoice")
    # def onchange_is_bad_debt_invoice(self):
    #     if self.is_bad_debt_invoice and self.refund_invoice_id:
    #         self.invoice_bad_debt_iic_ref = self.refund_invoice_id.iic_code
    #         self.invoice_bad_debt_issue_date_time = self.refund_invoice_id.header_send_datetime

    # number = self.env['ir.sequence'].next_by_code('account.einvoice.sequence.number')
    # rec.invoice_order_number = number
    # rec.invoice_number = str(number) + '/' + str(
    #     datetime.now().astimezone().replace(microsecond=0).year)
    #
    # seq_id = rec.journal_id.sequence_id.get_next_without_consume()
    # print(">>>>>>>>", seq_id)
    # print("_predict_nextval", _predict_nextval(self, seq_id))
    # return rec

    def make_invoice_qr_code(self, invoice_iic, invoice_issue_date_time, invoice_inv_ord_num, invoice_tot_price):
        # invoice_issuer_nuis = 'L62316009V'
        # invoice_busin_unit_code = "ll996sf167"
        # invoice_tcr_code = "vc813ms173"
        # invoice_soft_code = "bi558ej110"
        company_id = self.env.user.company_id
        invoice_issuer_nuis = company_id.vat
        invoice_busin_unit_code = self.operating_unit_id.business_unit_code
        invoice_soft_code = company_id.software_code
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=10,
            border=4,
        )
        # "https://efiskalizimi-app-test.tatime.gov.al/invoice-check/#/verify"
        inv_check_api_endpoint = company_id.invoice_check_endpoint
        qr.add_data(
            inv_check_api_endpoint +
            "?iic=" + invoice_iic +
            "&tin=" + invoice_issuer_nuis +
            "&crtd=" + invoice_issue_date_time +
            "&ord=" + invoice_inv_ord_num +
            "&bu=" + invoice_busin_unit_code +
            # "&cr=" + invoice_tcr_code +
            "&sw=" + invoice_soft_code +
            "&prc=" + str(invoice_tot_price)
        )
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        return qr_image

    def fiscalize_invoice(self):
        res = self
        coff = 1
        if res['move_type'] == 'out_refund':
            coff = -1

        company_id = self.env.user.company_id
        invoice_issuer_nuis = company_id.vat
        invoice_busin_unit_code = self.operating_unit_id.business_unit_code
        invoice_soft_code = company_id.software_code
        operator_code = self.user_id.operator_code
        if not operator_code:
            raise UserError("Provide Operator Code for the salesperson!")
        temp_dict = {
            'issuer_nuis': invoice_issuer_nuis,
            "busin_unit_code": invoice_busin_unit_code,
            # "tcr_code": "vc813ms173",
            "soft_code": invoice_soft_code,
            "operator_code": operator_code
        }
        # HEADER
        res['header_UUID'] = uuid.uuid4()
        res['header_send_datetime'] = datetime.utcnow().replace(tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()

        temp_dict['type_of_invoice'] = res['type_of_invoice']
        # temp_dict['type_of_invoice'] = dict(self._fields['type_of_invoice'].selection).get(res['type_of_invoice'])
        # temp_dict['type_of_self_iss'] = dict(self._fields['type_of_self_iss'].selection).get(
        #     res['type_of_self_iss'])
        temp_dict['type_of_self_iss'] = res['type_of_self_iss']

        # temp_dict['pay_method_type'] = dict(self._fields['pay_method_type'].selection).get(res['pay_method_type'])
        temp_dict['pay_method_type'] = res['pay_method_type']

        # temp_dict['invoice_seller_id_type'] = dict(self._fields['invoice_seller_id_type'].selection).get(
        #     res['invoice_seller_id_type'])

        temp_dict['invoice_seller_id_type'] = res['invoice_seller_id_type']
        temp_dict['invoice_buyer_id_type'] = res['invoice_buyer_id_type']

        temp_dict['invoice_same_tax_type_of_exempt_from_vat'] = res['invoice_same_tax_type_of_exempt_from_vat']

        temp_dict['invoice_order_number'] = res['invoice_order_number']
        temp_dict['invoice_number'] = res['invoice_number']
        temp_dict['company_id_is_in_vat'] = res['company_id']['company_id_is_in_vat']
        tax_free_amount = 0
        invoice_line_ids = res['invoice_line_ids'].filtered(lambda inv_line: not inv_line.display_type)
        if not company_id.company_id_is_in_vat:
            for line in invoice_line_ids:
                if not line.tax_ids:
                    tax_free_amount += line.price_subtotal
        temp_dict['invoice_tax_free_amount'] = str("{:.2f}".format(tax_free_amount * coff * res['currency_rate']))

        temp_dict['invoice_total_amount_without_vat'] = str("{:.2f}".format(
            float(res['amount_untaxed'] * coff * res['currency_rate'])))  # res['company_id']['vat_rate']

        # temp_dict['is_reverse_charge'] = res['company_id']['is_reverse_charge']
        temp_dict['is_reverse_charge'] = res['is_reverse_charge']
        temp_dict['due_date'] = res['invoice_date_due']
        temp_dict['pay_method_amount'] = str(
            "{:.2f}".format(float(res['amount_total'] * coff * res['currency_rate'])))  # res['amount_paid']
        if company_id.company_id_is_in_vat:
            temp_dict['vat_amt'] = str(
                "{:.2f}".format(
                    float(res['amount_tax'] * coff * res['currency_rate'])))  # res['company_id']['vat_rate']

            temp_dict['invoice_same_tax_number_of_items'] = str(len(invoice_line_ids))
            temp_dict['invoice_same_tax_price_before_vat'] = temp_dict['invoice_total_amount_without_vat']
            temp_dict['invoice_same_tax_vat_amount'] = temp_dict['vat_amt']
            temp_dict['invoice_same_tax_vat_rate'] = str("{:.2f}".format(float(0)))  # res['company_id']['vat_rate']

        # temp_dict['exrate'] = '123.50'  # TODO Check exchange Rate
        temp_dict['exrate'] = res.currency_rate
        temp_dict['invoice_seller_id_country'] = company_id.country_id.code_alpha3
        temp_dict['invoice_buyer_id_country'] = res.partner_id.country_id.code_alpha3
        temp_dict['invoice_seller_id_number'] = temp_dict['issuer_nuis']
        vals_dict = {field: getattr(res, field, None) for field in dir(res)}

        invoice_issuer_nuis = temp_dict['issuer_nuis']
        if not invoice_issuer_nuis:
            invoice_issuer_nuis = 'log-nipt-error'

        invoice_issue_date_time = res['header_send_datetime']  # TODO Check datetime
        if not invoice_issue_date_time:
            invoice_issue_date_time = datetime.utcnow().replace(
                tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
                microsecond=0).isoformat()
        invoice_inv_num = temp_dict['invoice_number']
        invoice_busin_unit_code = temp_dict['busin_unit_code']
        # invoice_tcr_code = temp_dict['tcr_code']
        invoice_soft_code = temp_dict['soft_code']
        invoice_tot_price = res['amount_total']
        if res['is_export']:
            res['invoice_goods_exported_amount'] = temp_dict['invoice_goods_exported_amount'] = str(
                "{:.2f}".format(float(res['amount_total']) * coff * res['currency_rate']))
        # if invoice_tot_price:
        invoice_tot_price = str("{:.2f}".format(float(invoice_tot_price)))
        iic_input = iic.build_iic_input(issuer_nipt=invoice_issuer_nuis,
                                        datetime_created=invoice_issue_date_time,
                                        invoice_number=invoice_inv_num,
                                        business_unit_code=invoice_busin_unit_code,
                                        # tcr_code=invoice_tcr_code,
                                        soft_code=invoice_soft_code,
                                        total_price=invoice_tot_price)
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')

        res['iic_code'] = temp_dict['invoice_iic'] = iic.generate_iic(iic_input=iic_input,
                                                                      company_p12_certificate=company_p12_certificate,
                                                                      certificate_password=certificate_password)
        res['iic_signature'] = temp_dict['invoice_iic_signature'] = iic.generate_iic_signature(iic_input=iic_input,
                                                                                               company_p12_certificate=company_p12_certificate,
                                                                                               certificate_password=certificate_password)
        # Special Case for Self Invoice

        if res['is_self_inv']:
            # For Buyer as Seller
            temp_dict["invoice_seller_id_number"] = res.partner_id.vat
            temp_dict["invoice_seller_id_type"] = res.partner_id.vat_type
            temp_dict["invoice_seller_id_name"] = res.partner_id.name
            temp_dict["invoice_seller_id_address"] = res.partner_id.street
            temp_dict["invoice_seller_id_city"] = res.partner_id.city
            temp_dict["invoice_seller_id_country"] = res.partner_id.country_id.code_alpha3

            # For Seller as Buyer
            temp_dict["invoice_buyer_id_number"] = company_id.vat
            temp_dict["invoice_buyer_id_type"] = company_id.partner_id.vat_type
            temp_dict["invoice_buyer_id_name"] = company_id.name
            temp_dict["invoice_buyer_id_address"] = company_id.street
            temp_dict["invoice_buyer_id_city"] = company_id.city
            temp_dict["invoice_buyer_id_country"] = company_id.country_id.code_alpha3

        vals_dict.update(temp_dict)

        # print("dwwww",base64.b64decode( company_p12_certificate))
        # print("PASS", company_id.certificate_password)

        # certificate = os.getenv('P12_LOCATION')
        # password = os.getenv('PRIVATE_PASSWORD').encode('utf-8')
        # p12 = open(certificate, 'rb').read()
        # print("paswd", password)
        # print("p12", p12)

        res['xml'] = make_invoice(data=vals_dict, company_p12_certificate=company_p12_certificate,
                                  certificate_password=certificate_password)
        print(">>>>>>>>>>", res['xml'])
        print()
        print()
        print()

        try:
            url = company_id.fiscalization_endpoint
            response = make_http_call(res['xml'], url)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise ValidationError(e)
        #
        if response:
            print("wwwwwwwwwwwwwwww", str(response))
            fic = None
            root = etree.fromstring(response)
            for element in root.iter('{https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema}FIC'):
                fic = element.text
            if fic:
                res['fic_number'] = fic
                res['is_fiscalized'] = True

            else:
                res['is_fiscalized'] = False
                for faultcode in root.iter('faultcode'):
                    error_code = 0
                    for detail in root.iter('detail'):
                        for code in detail.iter('code'):
                            if code.text:
                                error_code = int(code.text)
                    error_message = self.env['fiscalization.error.code'].search(
                        [("name", "=", error_code)]).error_message
                    if not error_message:
                        for faultstring in root.iter('faultstring'):
                            res['fiscalization_response'] = "Fault Code: %s \n Fault String: %s" % (
                                faultcode.text, faultstring.text)
                            raise ValidationError(
                                "Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))
                    else:
                        raise ValidationError("Fault Code: %s \n Fault String: %s" % (faultcode.text, error_message))

    def check_and_perform_fiscalization(self):
        for rec in self:
            if rec.name:
                if not rec.invoice_order_number and not rec.invoice_number:
                    print(" record.highest_name ", rec.highest_name, rec.sequence_number)
                    # next_seq_number = rec.journal_id.sequence_id.get_next_without_consume()
                    # if not next_seq_number:
                    #     raise ValidationError("There is some issue with the invoice sequence number. Contact Admin!")
                    inv_seq_number = rec.sequence_number
                    rec.invoice_order_number = inv_seq_number
                    rec.invoice_number = str(inv_seq_number) + '/' + str(
                        datetime.now().astimezone().replace(microsecond=0).year)
            if hasattr(self, "pos_order_ids"):
                pos_order_ids = self.pos_order_ids
            else:
                pos_order_ids = False

            if self.enable_fiscalization and not pos_order_ids:
                # self.enable_fiscalization = True
                # Skip pos order invoices
                # TODO check
                # pos_invoice_id = self.env['pos.order'].search([('invoice_id', '=', rec.id)])
                # if not pos_invoice_id and rec.move_type in ['out_invoice', 'out_refund']:
                if rec.move_type in ['out_invoice', 'out_refund']:
                    rec.fiscalize_invoice()
                    # import time
                    # time.sleep(2)
                    if rec.is_fiscalized and not rec.is_export and not rec.is_self_inv and rec.partner_id.vat_type not in [
                        'ID', 'PASS', 'SOC']:
                        if rec.move_type == 'out_invoice':
                            rec.e_invoice_reg()
                        elif rec.move_type == 'out_refund':
                            rec.credit_note_reg()

    def action_post(self):
        result = super(AccountInvoice, self).action_post()
        self.check_and_perform_fiscalization()
        return result

    def e_invoice_reg(self):
        xml_ubl_invoice_content = self.generate_ubl_xml_string().decode('utf-8')
        print("Registering E-invoice", xml_ubl_invoice_content)
        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')

        final_xml = e_invoice.make_e_invoice(xml_ubl_invoice_content, ubl_wrapper_tag="UblInvoice",
                                             company_p12_certificate=company_p12_certificate,
                                             certificate_password=certificate_password)
        url = company_id.einvoice_endpoint

        try:
            response = make_http_call(final_xml, url)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            # This is the correct syntax
            raise ValidationError(e)

        eic = None
        root = etree.fromstring(response)
        for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}EIC'):
            eic = element.text
            print(eic)
        if eic:
            self.eic_number = eic
        else:
            for faultcode in root.iter('faultcode'):
                for faultstring in root.iter('faultstring'):
                    self['fiscalization_response'] = "Fault Code: %s \n Fault String: %s" % (
                        faultcode.text, faultstring.text)

                    raise ValidationError("Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))

    def get_e_invoice_pdf(self):
        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')
        if self.eic_number:
            eic = self.eic_number
            final_xml = fetch_e_invoice.fetch_e_invoice(company_p12_certificate=company_p12_certificate,
                                                        certificate_password=certificate_password, eic=eic)
            url = company_id.einvoice_endpoint
            # print("URL", url)
            try:
                response = make_http_call(final_xml, url)

            except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                # This is the correct syntax
                raise ValidationError(e)

            print(response)
            # target_stream = io.BytesIO()

            pdf = None
            root = etree.fromstring(response)
            for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}Pdf'):
                pdf = element.text
            if pdf:
                self.output = pdf
                self.file_name = "E-Invoice " + self.name + ".pdf"
                url = "web/binary/download_pdf_document?model=account.move&rec_id={}&filename={}".format(self.id,
                                                                                                         self.file_name)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'download',
                    'tag': 'reload',
                }

    def get_ubl_lang(self):
        return self.partner_id.lang or 'en_US'

    # Supportive Methods
    @api.model
    def _ubl_get_nsmap_namespace(self, doc_name, version='2.1'):
        nsmap = {
            None: 'urn:oasis:names:specification:ubl:schema:xsd:' + doc_name,
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ns2': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
            'ns4': "urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2",
            'ns5': "http://www.w3.org/2000/09/xmldsig#",
            'ns6': "urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2",
            'ns7': "urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2",
        }
        ns = {
            'cac': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonAggregateComponents-2}',
            'cbc': '{urn:oasis:names:specification:ubl:schema:xsd:'
                   'CommonBasicComponents-2}',
            'ns2': "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}",
            'ns4': "{urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2}",
            'ns5': "{http://www.w3.org/2000/09/xmldsig#}",
            'ns6': "{urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2}",
            'ns7': "{urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2}",
        }
        return nsmap, ns

    def generate_invoice_ubl_xml_etree(self, version='2.1'):
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        self._ubl_add_header(xml_root, ns, version=version)
        # self._ubl_add_order_reference(xml_root, ns, version=version)
        # self._ubl_add_contract_document_reference(
        #     xml_root, ns, version=version)
        # self._ubl_add_attachments(xml_root, ns, version=version)
        self._ubl_invoice_period(self.start_date, self.end_date, "InvoicePeriod", xml_root, ns, version=version)
        if self.transporter_id:
            transporter_name = "Transporter: %s, " % self.transporter_id.display_name
            transporter_vat = ""
            if self.transporter_id.vat:
                transporter_vat = "%s, " % self.transporter_id.vat
            plate_no = "%s, " % self.license_plate_no
            date = "%s" % self.delivery_datetime

            despatch_document_reference = transporter_name + transporter_vat + plate_no + date
            self._ubl_despatch_document_reference(despatch_document_reference, "DespatchDocumentReference", xml_root,
                                                  ns,
                                                  version=version)

        for attach_doc_id in self.attach_doc_ids:
            self._ubl_add_additional_doc_ref(attach_doc_id, "AdditionalDocumentReference", xml_root, ns,
                                             version=version)

        for attach_doc_id in self.attach_doc_link_ids:
            self._ubl_add_additional_doc_ref_links(attach_doc_id, "AdditionalDocumentReference", xml_root, ns,
                                                   version=version)
        self._ubl_add_supplier_party(False, self.company_id, 'AccountingSupplierParty', xml_root, ns, version=version)

        self._ubl_add_customer_party(self.partner_id, False, 'AccountingCustomerParty', xml_root, ns, version=version)
        # # the field 'partner_shipping_id' is defined in the 'sale' module
        # if hasattr(self, 'partner_shipping_id') and self.partner_shipping_id:
        #     self._ubl_add_delivery(self.partner_shipping_id, xml_root, ns)

        # Put paymentmeans block even when invoice is paid ?
        # payment_identifier = self.get_payment_identifier()
        payment_mode_id = None  # TODO May be updated later
        # For main bank
        self._ubl_add_payment_means(self.partner_bank_id, payment_mode_id, self.invoice_date_due, xml_root, ns,
                                    payment_identifier=None, version=version)
        # For additional banks
        for additional_bank_id in self.partner_additional_bank_ids:
            self._ubl_add_payment_means(additional_bank_id, payment_mode_id, self.invoice_date_due, xml_root, ns,
                                        payment_identifier=None, version=version)
        if self.invoice_payment_term_id:
            self._ubl_add_payment_terms(self.invoice_payment_term_id, xml_root, ns, version=version)

        # self._ubl_add_doc_level_allowance_charge(xml_root, ns, version=version, charge=False) # TODO Check document level charges
        # self._ubl_add_allowance_charge(xml_root, ns, version=version, charge=True)

        self._ubl_add_tax_total(xml_root, ns, version=version)

        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        invoice_line_ids = self.invoice_line_ids.filtered(lambda inv_line: not inv_line.display_type)
        for iline in invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(xml_root, iline, line_number, ns, version=version)
        return xml_root

    def _ubl_add_invoice_line(self, parent_node, iline, line_number, ns, version='2.1'):
        cur_name = self.currency_id.name
        coff = 1
        if self.move_type == 'out_invoice':
            line_root_name = "InvoiceLine"
            line_qty_element_name = "InvoicedQuantity"
            coff = 1
        elif self.move_type == 'out_refund':
            line_root_name = "CreditNoteLine"
            line_qty_element_name = "CreditedQuantity"
            coff = -1

        line_root = etree.SubElement(parent_node, ns['cac'] + line_root_name)
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        price_precision = dpo.precision_get('Product Price')
        account_precision = self.currency_id.decimal_places
        line_id = etree.SubElement(line_root, ns['cbc'] + 'ID')
        line_id.text = str(line_number)
        uom_unece_code = False
        # uom_id is not a required field on account.move.line
        if iline.product_uom_id and iline.product_uom_id.unece_code:
            uom_unece_code = iline.product_uom_id.unece_code
        if uom_unece_code:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + line_qty_element_name,
                unitCode=uom_unece_code)
        else:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + line_qty_element_name)
        qty = iline.quantity
        quantity.text = '%0.*f' % (qty_precision, qty * coff)
        line_amount = etree.SubElement(
            line_root, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        tax_calc = iline.tax_ids.compute_all(iline.price_unit, self.currency_id,
                                             iline.quantity, product=None, partner=None)
        total_excluded = tax_calc['total_excluded']

        line_amount.text = '%0.*f' % (2, (iline.price_subtotal * coff))
        # line_amount.text = '%0.*f' % (2, (iline.price_unit * iline.quantity * coff))
        # line_amount.text = '%0.*f' % (2, (iline.price_subtotal * coff))

        # self._ubl_add_line_level_allowance_charge(line_root, iline, ns, version=version, charge=False)
        # self._ubl_add_allowance_charge(line_root, ns, version=version, charge=True)

        # self._ubl_add_invoice_line_tax_total(iline, line_root, ns, version=version)

        self._ubl_add_item(iline, iline.name, iline.product_id, line_root, ns, type='sale', version=version)

        price_node = etree.SubElement(line_root, ns['cac'] + 'Price')
        price_amount = etree.SubElement(price_node, ns['cbc'] + 'PriceAmount', currencyID=cur_name)
        price_unit = 0.0
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        if not float_is_zero(qty, precision_digits=qty_precision):
            price_unit = float_round(
                iline.price_subtotal / float(qty),
                precision_digits=price_precision)
        price_amount.text = '%0.*f' % (price_precision, price_unit)
        if uom_unece_code:
            base_qty = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity', unitCode=uom_unece_code)
        else:
            base_qty = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity')
        base_qty.text = '%0.*f' % (qty_precision, qty * coff)

        self._ubl_add_price_level_allowance_charge(price_node, iline, ns, version=version, charge=False)
        # self._ubl_add_allowance_charge(price_node, ns, version=version, charge=True)

    def _ubl_add_invoice_line_tax_total(self, iline, parent_node, ns, version='2.1'):
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        tax_total_node = etree.SubElement(parent_node, ns['cac'] + 'TaxTotal')
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        res_taxes = iline.tax_ids.compute_all(
            price, quantity=iline.quantity, product=iline.product_id,
            partner=self.partner_id)
        tax_total = float_round(
            res_taxes['total_included'] - res_taxes['total_excluded'],
            precision_digits=prec)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = '%0.*f' % (2, tax_total)
        if not float_is_zero(tax_total, precision_digits=prec):
            for res_tax in res_taxes['taxes']:
                tax = self.env['account.tax'].browse(res_tax['id'])
                # we don't have the base amount in res_tax :-(
                self._ubl_add_tax_subtotal(res_tax['base'], res_tax['amount'], tax, cur_name, tax_total_node, ns,
                                           version=version)

    def _ubl_add_legal_monetary_total(self, parent_node, ns, version='2.1'):
        monetary_total = etree.SubElement(parent_node, ns['cac'] + 'LegalMonetaryTotal')
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        total_line_extension_amount = 0
        currency_id = self.currency_id
        invoice_line_ids = self.invoice_line_ids.filtered(lambda inv_line: not inv_line.display_type)
        for invoice_line in invoice_line_ids:
            # line_extension_amount = invoice_line.quantity * invoice_line.price_unit
            # line_extension_amount = invoice_line.price_subtotal
            # total_line_extension_amount += line_extension_amount

            tax_calc = invoice_line.tax_ids.compute_all(invoice_line.price_unit, currency_id,
                                                        invoice_line.quantity, product=None, partner=None)
            total_excluded = tax_calc['total_excluded']
            total_line_extension_amount += total_excluded
        line_total = etree.SubElement(monetary_total, ns['cbc'] + 'LineExtensionAmount', currencyID=cur_name)
        if self.move_type == 'out_invoice':
            line_total.text = '%0.*f' % (prec, self.amount_untaxed)  # total_line_extension_amount
        elif self.move_type == 'out_refund':
            line_total.text = '%0.*f' % (prec, self.amount_untaxed * -1)  # total_line_extension_amount

        tax_excl_total = etree.SubElement(monetary_total, ns['cbc'] + 'TaxExclusiveAmount', currencyID=cur_name)
        if self.move_type == 'out_invoice':
            tax_excl_total.text = '%0.*f' % (prec, self.amount_untaxed)
        elif self.move_type == 'out_refund':
            tax_excl_total.text = '%0.*f' % (prec, self.amount_untaxed * -1)

        tax_incl_total = etree.SubElement(monetary_total, ns['cbc'] + 'TaxInclusiveAmount', currencyID=cur_name)
        if self.move_type == 'out_invoice':
            tax_incl_total.text = '%0.*f' % (prec, self.amount_total)
        elif self.move_type == 'out_refund':
            tax_incl_total.text = '%0.*f' % (prec, self.amount_total * -1)
        total_discount_amount = 0
        # for invoice_line in self.invoice_line_ids:
        #     if invoice_line.discount:
        #         tax_calc = invoice_line.tax_ids.compute_all(invoice_line.price_unit, currency_id,
        #                                                                  1, product=None,
        #                                                                  partner=None)
        #         total_excluded = tax_calc['total_excluded']
        #
        #         discount_amount = (total_excluded * (invoice_line.discount / 100)) * invoice_line.quantity
        #         total_discount_amount += discount_amount

        allowance_total_amount = etree.SubElement(monetary_total, ns['cbc'] + 'AllowanceTotalAmount',
                                                  currencyID=cur_name)
        allowance_total_amount.text = str(round(total_discount_amount, 2))
        #
        # charge_total_amount = etree.SubElement(monetary_total, ns['cbc'] + 'ChargeTotalAmount', currencyID=cur_name)
        # charge_total_amount.text = '%0.*f' % (prec, 0)

        prepaid_value = self.amount_total - self.amount_residual
        if prepaid_value:
            prepaid_amount = etree.SubElement(monetary_total, ns['cbc'] + 'PrepaidAmount', currencyID=cur_name)
            if self.move_type == 'out_invoice':
                prepaid_amount.text = '%0.*f' % (prec, prepaid_value)
            elif self.move_type == 'out_refund':
                prepaid_amount.text = '%0.*f' % (prec, prepaid_value * -1)

        payable_amount = etree.SubElement(monetary_total, ns['cbc'] + 'PayableAmount', currencyID=cur_name)
        if self.move_type == 'out_invoice':
            payable_amount.text = '%0.*f' % (prec, self.amount_residual)
        elif self.move_type == 'out_refund':
            payable_amount.text = '%0.*f' % (prec, (self.amount_residual * -1) if self.amount_residual else 0.0)

    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        self.ensure_one()
        cur_name = self.currency_id.name
        # tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        # tax_amount_node = etree.SubElement(tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        # prec = self.currency_id.decimal_places
        # tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)

        tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        tax_amount_node = etree.SubElement(tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        prec = self.currency_id.decimal_places
        # tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
        if self.move_type == 'out_invoice':
            tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
        elif self.move_type == 'out_refund':
            tax_amount_node.text = '%0.*f' % (prec, self.amount_tax * -1)

        # print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&", self.tax_line_ids)
        # if not float_is_zero(self.amount_tax, precision_digits=prec):
        for tline in self.tax_line_ids:
            print("tline.amount", tline.amount)
            self._ubl_add_tax_subtotal(tline.base, tline.amount, tline.tax_id, cur_name, tax_total_node, ns,
                                       version=version)
        lines_without_tax = self.invoice_line_ids.filtered(
            lambda line: not line.tax_ids and not line.display_type)

        if lines_without_tax:
            total_sub = 0
            for ln in lines_without_tax:
                total_sub += ln.price_subtotal
            prec = self.env['decimal.precision'].precision_get('Account')
            tax_subtotal = etree.SubElement(tax_total_node, ns['cac'] + 'TaxSubtotal')
            # if not float_is_zero(taxable_amount, precision_digits=prec):
            taxable_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxableAmount',
                                                   currencyID=cur_name)
            if self.move_type == 'out_invoice':
                taxable_amount_node.text = '%0.*f' % (2, total_sub)
            elif self.move_type == 'out_refund':
                taxable_amount_node.text = '%0.*f' % (2, total_sub * -1)

            tax_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
            # if self.type == 'out_invoice':
            tax_amount_node.text = '%0.*f' % (2, 0)
            # elif self.type == 'out_refund':
            #     tax_amount_node.text = '%0.*f' % (2, tax_amount * -1)

            tax_category = etree.SubElement(tax_subtotal, ns['cac'] + 'TaxCategory')
            # if not tax.unece_categ_id:
            #     raise UserError(_(
            #         "Missing UNECE Tax Category on tax '%s'" % tax.name))
            tax_category_id = etree.SubElement(tax_category, ns['cbc'] + 'ID')
            tax_category_id.text = "O"
            tax_exemption_reason = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
            tax_exemption_reason.text = "VATEX-EU-132"
            # tax_name = etree.SubElement(
            #     tax_category, ns['cbc'] + 'Name')
            # tax_name.text = tax.name
            # if tax.amount_type == 'percent':
            # tax_percent = etree.SubElement(
            #     tax_category, ns['cbc'] + 'Percent')
            # tax_percent.text = '%0.*f' % (2, 0)  # str(tax.amount)
            # tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
            # self._ubl_add_tax_scheme(tax_scheme_dict, tax_category, ns, version=version)

            tax_scheme = etree.SubElement(tax_category, ns['cac'] + 'TaxScheme')
            # if tax_scheme_dict.get('id'):
            tax_scheme_id = etree.SubElement(tax_scheme, ns['cbc'] + 'ID')
            tax_scheme_id.text = "VAT"

        # ************Used for foreign currency only***********
        if cur_name != "ALL":
            tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
            tax_amount_node = etree.SubElement(tax_total_node, ns['cbc'] + 'TaxAmount',
                                               currencyID="ALL")  # TODO Used static may be updated later
            prec = self.currency_id.decimal_places
            # tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
            to_currency_id = self.env['res.currency'].search([('name', '=', 'ALL')])
            amount_tax = self.amount_tax
            if to_currency_id:
                # amount_tax = self.currency_id._convert(amount_tax, to_currency_id, self.company_id,
                #                                        datetime.today())
                amount_tax = amount_tax * self.currency_rate
            if self.move_type == 'out_invoice':
                tax_amount_node.text = '%0.*f' % (prec, amount_tax)
            elif self.move_type == 'out_refund':
                tax_amount_node.text = '%0.*f' % (prec, amount_tax * -1)

        #     *************************************************

    def _ubl_add_doc_level_allowance_charge(self, xml_root, ns, version='2.1', charge=False):
        self.ensure_one()
        cur_name = self.currency_id.name

        prec = self.currency_id.decimal_places
        invoice_line_ids = self.invoice_line_ids.filtered(lambda inv_line: not inv_line.display_type)
        for invoice_line in invoice_line_ids:
            if invoice_line.discount:
                allowance_charge_node = etree.SubElement(xml_root, ns['cac'] + 'AllowanceCharge')
                charge_indicator_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'ChargeIndicator')
                charge_indicator_node.text = "true" if charge else 'false'
                charge_allowance_reason_node = etree.SubElement(allowance_charge_node,
                                                                ns['cbc'] + "AllowanceChargeReason")
                charge_allowance_reason_node.text = "Volume Discount"  # TODO Update with dynamic value

                multiplier_factor_numeric_node = etree.SubElement(allowance_charge_node,
                                                                  ns['cbc'] + 'MultiplierFactorNumeric')
                multiplier_factor_numeric_node.text = str(round(invoice_line.discount, 2))

                tax_calc = invoice_line.tax_ids.compute_all(invoice_line.price_unit, self.currency_id,
                                                            1, product=None,
                                                            partner=None)
                total_excluded = tax_calc['total_excluded']
                discount_amount = (total_excluded * (invoice_line.discount / 100)) * invoice_line.quantity
                amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'Amount', currencyID=cur_name)
                amount_node.text = str(round(discount_amount, 2))

                base_amount = (total_excluded * invoice_line.quantity)
                base_amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'BaseAmount',
                                                    currencyID=cur_name)
                base_amount_node.text = str(round(base_amount, 2))
                for tax_id in invoice_line.tax_ids:
                    self._ubl_add_tax_category(tax_id, allowance_charge_node, ns, version=version)
                if not invoice_line.tax_ids:
                    # print(">>>>>>>>>>>>> RUNNING ELSE PART")
                    # total_sub = 0
                    # for ln in lines_without_tax:
                    #     total_sub += ln.price_subtotal
                    # prec = self.env['decimal.precision'].precision_get('Account')
                    # tax_subtotal = etree.SubElement(tax_total_node, ns['cac'] + 'TaxSubtotal')
                    # if not float_is_zero(taxable_amount, precision_digits=prec):
                    # taxable_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxableAmount',
                    #                                        currencyID=cur_name)
                    # if self.type == 'out_invoice':
                    # taxable_amount_node.text = '%0.*f' % (2, total_sub)
                    # elif self.type == 'out_refund':
                    #         taxable_amount_node.text = '%0.*f' % (2, taxable_amount * -1)

                    # tax_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
                    # if self.type == 'out_invoice':
                    # tax_amount_node.text = '%0.*f' % (2, 0)
                    # elif self.type == 'out_refund':
                    #     tax_amount_node.text = '%0.*f' % (2, tax_amount * -1)

                    tax_category = etree.SubElement(allowance_charge_node, ns['cac'] + 'TaxCategory')
                    # if not tax.unece_categ_id:
                    #     raise UserError(_(
                    #         "Missing UNECE Tax Category on tax '%s'" % tax.name))
                    tax_category_id = etree.SubElement(tax_category, ns['cbc'] + 'ID')
                    tax_category_id.text = "O"
                    # tax_exemption_reason = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
                    # tax_exemption_reason.text = "VATEX-EU-132"
                    # tax_name = etree.SubElement(
                    #     tax_category, ns['cbc'] + 'Name')
                    # tax_name.text = tax.name
                    # if tax.amount_type == 'percent':
                    # tax_percent = etree.SubElement(
                    #     tax_category, ns['cbc'] + 'Percent')
                    # tax_percent.text = '%0.*f' % (2, 0)  # str(tax.amount)
                    # tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
                    # self._ubl_add_tax_scheme(tax_scheme_dict, tax_category, ns, version=version)

                    tax_scheme = etree.SubElement(tax_category, ns['cac'] + 'TaxScheme')
                    # if tax_scheme_dict.get('id'):
                    tax_scheme_id = etree.SubElement(tax_scheme, ns['cbc'] + 'ID')
                    tax_scheme_id.text = "VAT"

        # if not float_is_zero(self.amount_tax, precision_digits=prec):
        #     for tline in self.tax_line_ids:
        #         allowance_charge_node = etree.SubElement(xml_root, ns['cac'] + 'AllowanceCharge')
        #         charge_indicator_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'ChargeIndicator')
        #         charge_indicator_node.text = "true" if charge else 'false'
        #
        #         charge_allowance_reason_node = etree.SubElement(allowance_charge_node,
        #                                                         ns['cbc'] + 'AllowanceChargeReason')
        #         charge_allowance_reason_node.text = "Testing Reason"
        #
        #         amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'Amount', currencyID=cur_name)
        #         amount_node.text = "0.00"
        #         self._ubl_add_tax_category(tline.tax_id, allowance_charge_node, ns, version=version)

    def _ubl_add_line_level_allowance_charge(self, xml_root, iline, ns, version='2.1', charge=False):
        self.ensure_one()
        cur_name = self.currency_id.name

        prec = self.currency_id.decimal_places
        invoice_line = iline
        if invoice_line:
            if invoice_line.discount:
                allowance_charge_node = etree.SubElement(xml_root, ns['cac'] + 'AllowanceCharge')
                charge_indicator_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'ChargeIndicator')
                charge_indicator_node.text = "true" if charge else 'false'

                charge_allowance_reason_node = etree.SubElement(allowance_charge_node,
                                                                ns['cbc'] + 'AllowanceChargeReason')
                charge_allowance_reason_node.text = "Volume Discount"

                multiplier_factor_numeric_node = etree.SubElement(allowance_charge_node,
                                                                  ns['cbc'] + 'MultiplierFactorNumeric')
                multiplier_factor_numeric_node.text = str(round(invoice_line.discount, 2))

                tax_calc = invoice_line.tax_ids.compute_all(invoice_line.price_unit, self.currency_id,
                                                            1, product=None,
                                                            partner=None)
                total_excluded = tax_calc['total_excluded']

                discount_amount = (total_excluded * (invoice_line.discount / 100)) * invoice_line.quantity
                amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'Amount', currencyID=cur_name)
                amount_node.text = str(round(discount_amount, 2))

                base_amount = (total_excluded * invoice_line.quantity)
                base_amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'BaseAmount',
                                                    currencyID=cur_name)
                base_amount_node.text = str(round(base_amount, 2))
                # for tax_id in invoice_line.tax_ids:
                #     self._ubl_add_tax_category(tax_id, allowance_charge_node, ns, version=version)

        # if not float_is_zero(self.amount_tax, precision_digits=prec):
        #     for tline in self.tax_line_ids:
        #         allowance_charge_node = etree.SubElement(xml_root, ns['cac'] + 'AllowanceCharge')
        #         charge_indicator_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'ChargeIndicator')
        #         charge_indicator_node.text = "true" if charge else 'false'
        #
        #         charge_allowance_reason_node = etree.SubElement(allowance_charge_node,
        #                                                         ns['cbc'] + 'AllowanceChargeReason')
        #         charge_allowance_reason_node.text = "Testing Reason"
        #
        #         amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'Amount', currencyID=cur_name)
        #         amount_node.text = "0.00"
        #         self._ubl_add_tax_category(tline.tax_id, allowance_charge_node, ns, version=version)

    def _ubl_add_price_level_allowance_charge(self, xml_root, iline, ns, version='2.1', charge=False):
        self.ensure_one()
        cur_name = self.currency_id.name

        prec = self.currency_id.decimal_places
        invoice_line = iline
        if invoice_line:
            if invoice_line.discount:
                allowance_charge_node = etree.SubElement(xml_root, ns['cac'] + 'AllowanceCharge')
                charge_indicator_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'ChargeIndicator')
                charge_indicator_node.text = "true" if charge else 'false'

                # charge_allowance_reason_node = etree.SubElement(allowance_charge_node,
                #                                                 ns['cbc'] + 'AllowanceChargeReason')
                # charge_allowance_reason_node.text = "Volume Discount"
                #
                # multiplier_factor_numeric_node = etree.SubElement(allowance_charge_node,
                #                                                   ns['cbc'] + 'MultiplierFactorNumeric')
                # multiplier_factor_numeric_node.text = str(round(invoice_line.discount, 2))
                tax_calc = invoice_line.tax_ids.compute_all(invoice_line.price_unit, self.currency_id,
                                                            1, product=None,
                                                            partner=None)
                total_excluded = tax_calc['total_excluded']

                discount_amount = (total_excluded * (invoice_line.discount / 100)) * invoice_line.quantity
                amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'Amount', currencyID=cur_name)
                amount_node.text = str(round(discount_amount, 2))

                base_amount = (total_excluded * invoice_line.quantity)
                base_amount_node = etree.SubElement(allowance_charge_node, ns['cbc'] + 'BaseAmount',
                                                    currencyID=cur_name)
                base_amount_node.text = str(round(base_amount, 2))

    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        ubl_extensions = etree.SubElement(parent_node, ns['ns2'] + "UBLExtensions")
        ubl_extension = etree.SubElement(ubl_extensions, ns['ns2'] + "UBLExtension")
        extension_content = etree.SubElement(ubl_extension, ns['ns2'] + "ExtensionContent")
        ubl_doc_signature = etree.SubElement(extension_content, ns['ns7'] + "UBLDocumentSignatures")
        signature_info = etree.SubElement(ubl_doc_signature, ns['ns6'] + "SignatureInformation")
        signature = etree.SubElement(signature_info, ns['ns5'] + "Signature", Id='placeholder')

        ubl_version = etree.SubElement(parent_node, ns['cbc'] + 'UBLVersionID')
        ubl_version.text = version
        customization_id = etree.SubElement(parent_node, ns['cbc'] + 'CustomizationID')
        customization_id.text = "urn:cen.eu:en16931:2017"

        profile_id = etree.SubElement(parent_node, ns['cbc'] + 'ProfileID')
        profile_id.text = self.business_process
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        doc_id.text = self.invoice_number
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        issue_date.text = self.invoice_date.strftime('%Y-%m-%d')

        if self.move_type == 'out_invoice':
            due_date = etree.SubElement(parent_node, ns['cbc'] + "DueDate")
            due_date.text = self.invoice_date_due.strftime('%Y-%m-%d')
            # profile_id.text = "P1"
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + 'InvoiceTypeCode')
            type_code.text = self.type_code

        elif self.move_type == 'out_refund':
            # profile_id.text = "P10"
            type_code = etree.SubElement(
                parent_node, ns['cbc'] + "CreditNoteTypeCode")
            type_code.text = self.type_code
        # mandatory note elements
        iic_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        iic_note.text = "IIC=" + self.iic_code

        iic_signature_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        iic_signature_note.text = "IICSignature=" + self.iic_signature

        fic_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        fic_note.text = "FIC=" + self.fic_number

        issue_date_time_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        invoice_issue_date_time = self.invoice_datetime
        if not invoice_issue_date_time:
            invoice_issue_date_time = datetime.utcnow().replace(tzinfo=from_zone).astimezone(to_zone).replace(
                microsecond=0).isoformat()
        if invoice_issue_date_time:
            issue_date_time_note.text = "IssueDateTime=" + str(invoice_issue_date_time)

        company_id = self.env.user.company_id
        invoice_busin_unit_code = self.operating_unit_id.business_unit_code
        invoice_soft_code = company_id.software_code
        operator_code = self.user_id.operator_code

        operator_code_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        operator_code_note.text = "OperatorCode=" + operator_code

        business_unit_code_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        business_unit_code_note.text = "BusinessUnitCode=" + invoice_busin_unit_code

        software_code_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        software_code_note.text = "SoftwareCode=" + invoice_soft_code

        is_bad_debt_inv_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
        if self.is_bad_debt_invoice:
            is_bad_debt_inv_note.text = "IsBadDebtInv=true"
        else:
            is_bad_debt_inv_note.text = "IsBadDebtInv=false"

        if self.currency_id.name != "ALL":
            currency_exchange_rate_note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            currency_exchange_rate_note.text = "CurrencyExchangeRate=" + '%0.*f' % (2, self.currency_id.inverse_rate)

        if self.narration:
            note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note.text = self.narration
        doc_currency = etree.SubElement(parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name

        tax_currency_code = etree.SubElement(parent_node, ns['cbc'] + 'TaxCurrencyCode')
        tax_currency_code.text = "ALL"

    def generate_ubl_xml_string(self, version='2.1'):
        self.ensure_one()
        assert self.state in ("posted")
        assert self.move_type in 'out_invoice'
        # logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()

        xml_root = self.with_context(lang=lang).generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(xml_root, pretty_print=True, encoding='UTF-8', xml_declaration=False)

        return xml_string

    #     For Credit Note
    def credit_note_reg(self):
        print("CREDIT NOTE REG")
        xml_credit_note_ubl_invoice_content = self.generate_credit_note_ubl_xml_string().decode('utf-8')
        print("Registering CREDIT NOTE", xml_credit_note_ubl_invoice_content)
        _logger.info("Registering CREDIT NOTE %s " % xml_credit_note_ubl_invoice_content)
        # response = e_invoice.make_e_invoice(xml_credit_note_ubl_invoice_content, ubl_wrapper_tag="UblCreditNote")

        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')

        final_xml = e_invoice.make_e_invoice(xml_credit_note_ubl_invoice_content, ubl_wrapper_tag="UblCreditNote",
                                             company_p12_certificate=company_p12_certificate,
                                             certificate_password=certificate_password)
        url = company_id.einvoice_endpoint
        try:
            response = make_http_call(final_xml, url)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            # This is the correct syntax
            raise ValidationError(e)

        eic = None
        root = etree.fromstring(response)
        for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}EIC'):
            eic = element.text
            print(eic)
        if eic:
            self.eic_number = eic
        else:
            for faultcode in root.iter('faultcode'):
                for faultstring in root.iter('faultstring'):
                    self['fiscalization_response'] = "Fault Code: %s \n Fault String: %s" % (
                        faultcode.text, faultstring.text)

                    raise ValidationError("Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))

    def generate_credit_note_ubl_xml_string(self, version='2.1'):
        self.ensure_one()
        assert self.state in ("posted")
        assert self.move_type in 'out_refund'
        # logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        xml_root = self.with_context(lang=lang).generate_credit_note_ubl_xml_etree(version=version)
        xml_string = etree.tostring(xml_root, pretty_print=True, encoding='UTF-8', xml_declaration=False)
        return xml_string

    def generate_credit_note_ubl_xml_etree(self, version='2.1'):
        nsmap, ns = self._ubl_get_nsmap_namespace('CreditNote-2', version=version)
        xml_root = etree.Element('CreditNote', nsmap=nsmap)
        self._ubl_add_header(xml_root, ns, version=version)
        self._ubl_invoice_period(self.start_date, self.end_date, "InvoicePeriod", xml_root, ns, version=version)
        self._ubl_add_supplier_party(False, self.company_id, 'AccountingSupplierParty', xml_root, ns, version=version)
        self._ubl_add_customer_party(self.partner_id, False, 'AccountingCustomerParty', xml_root, ns, version=version)

        payment_mode_id = None  # TODO May be updated later
        self._ubl_add_payment_means(self.partner_bank_id, payment_mode_id, self.invoice_date_due, xml_root, ns,
                                    payment_identifier=None, version=version)
        if self.invoice_payment_term_id:
            self._ubl_add_payment_terms(self.invoice_payment_term_id, xml_root, ns, version=version)

        # self._ubl_add_doc_level_allowance_charge(xml_root, ns, version=version, charge=False)
        # self._ubl_add_allowance_charge(xml_root, ns, version=version, charge=True)

        self._ubl_add_tax_total(xml_root, ns, version=version)

        self._ubl_add_legal_monetary_total(xml_root, ns, version=version)

        line_number = 0
        invoice_line_ids = self.invoice_line_ids.filtered(lambda inv_line: not inv_line.display_type)
        for iline in invoice_line_ids:
            line_number += 1
            self._ubl_add_invoice_line(xml_root, iline, line_number, ns, version=version)
        return xml_root


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    # INVOICE ITEMS

    # invoice_item_name = fields.Char(related='name', size=50)
    # invoice_item_code = fields.Char(related='product_id.barcode', size=50)
    invoice_item_unit_of_measure = fields.Char(related='product_id.uom_id.name', size=50)
    company_is_vat_register = fields.Boolean(related="company_id.company_id_is_in_vat")

    # invoice_item_quantity = fields.Float(digits=(12, 3))  # qty
    # invoice_item_unit_price_before_vat = fields.Float(digits=(12, 2))  # price_subtotal/qty
    # invoice_item_unit_price_after_vat = fields.Float(digits=(12, 2))  # price_unit
    # invoice_item_rebate = fields.Float(digits=(12, 2))  # discount
    # does_item_rebate_reduce_base_price = fields.Boolean("A e ul zbritja shumen e bazes tatimore?")
    # invoice_item_vat_rate = fields.Float(digits=(12, 2))  # tax_ids_after_fiscal_position
    # invoice_item_type_of_exempt_from_vat = fields.Selection(selection=[('type_1', 'TYPE_1'),
    #                                                                    ('type_2', 'TYPE_2'),
    #                                                                    ('tax_free', 'TAX_FREE'),
    #                                                                    ('margin_scheme', 'MARGIN_SCHEME'),
    #                                                                    ('export_of_goods', 'EXPORT_OF_GOODS')],
    #                                                         default='type_1')  # not applicable for the moment
    # invoice_item_vat_amount = fields.Float(digits=(12, 2))  # price_subtotal_incl-price_subtotal
    # invoice_item_is_investment = fields.Boolean("A jane artikujt e blere investim?")
    # invoice_item_price_after_vat_apply = fields.Float(digits=(12, 2))  # price_subtotal_incl

    @api.constrains('tax_ids')
    @api.onchange('tax_ids')
    def _check_limit(self):
        for rec in self:
            if len(rec.tax_ids) > 1:
                raise ValidationError("Only one tax can be applied!!!")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sanitized_vat = fields.Char(
        compute='_compute_sanitized_vat', string='Sanitized TIN',
        store=True, readonly=True,
        help='TIN in uppercase without spaces nor special characters.')

    # license_plate_no = fields.Char()

    @classmethod
    def _sanitize_vat(cls, vat):
        return vat and re.sub(r'\W+', '', vat).upper() or False

    @api.depends('vat')
    def _compute_sanitized_vat(self):
        for partner in self:
            # print("Partner Vat", partner.vat, partner.commercial_partner_id)
            partner.sanitized_vat = self._sanitize_vat(partner.vat)


class UomUom(models.Model):
    _inherit = 'uom.uom'

    unece_code = fields.Char(
        string='UNECE Code',
        help="Standard nomenclature of the United Nations Economic "
             "Commission for Europe (UNECE).")


class BinaryDownload(http.Controller):
    @http.route('/web/binary/download_pdf_document', type='http', auth='public')
    def download_document(self, model, rec_id, filename=None, **kwargs):
        record_id = request.env[model].sudo().browse(int(rec_id))
        binary_file = record_id.output
        file_content = base64.b64decode(binary_file or "")
        if not file_content:
            return request.not_found()
        else:
            if not filename:
                filename = "E-Invoice" + ".pdf"

            content_type = ('Content-Type', 'application/pdf')
            disposition_content = ('Content-Disposition', content_disposition(filename))
            return request.make_response(file_content, [content_type, disposition_content])


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    for_export = fields.Boolean("Use For Export")
    for_self_inv = fields.Boolean("Use For Self Invoice")
    for_reverse_charge = fields.Boolean("Use For Reverse Charge")

    @api.onchange("for_reverse_charge")
    def onchange_for_reverse_charge(self):
        if self.for_reverse_charge:
            self.for_self_inv = True
        else:
            self.for_self_inv = False


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains('taxes_id')
    @api.onchange('taxes_id')
    def _check_limit(self):
        for rec in self:
            if len(rec.taxes_id) > 1:
                raise ValidationError("Only one tax can be applied!!!")


class FiscalizationErrorCodes(models.Model):
    _name = "fiscalization.error.code"

    name = fields.Integer("Error Code")
    error_message = fields.Text()
