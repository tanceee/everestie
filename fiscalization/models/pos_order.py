import uuid
from datetime import datetime, timedelta

from dateutil import tz

from odoo import api, fields, models, http
from ..services.http_calls.request import make_http_call
from ..services.http_calls.response import parse_response
from ..services.invoice import make_invoice
from ..services.qr_codes.make_invoice_qr_code import make_invoice_qr_code
from odoo.exceptions import ValidationError, UserError
import base64
import logging
import requests

_logger = logging.getLogger(__name__)

from_zone = tz.gettz('UTC')
to_zone = tz.gettz('Europe/Tirane')


# class resUsers(models.Model):
#     _inherit = 'res.users'
#
#     operator_code = fields.Char("Operator Code", size=10)


class PosOrder(models.Model):
    _inherit = "pos.order"

    # HEADER
    header_UUID = fields.Char(string="Header UUID", readonly=True, copy=False)
    header_send_datetime = fields.Char("Header Date Time", readonly=True, copy=False)
    header_subseq_delivery_type = fields.Selection(selection=[('no_internet', 'NOINTERNET'),
                                                              ('bound_book', 'BOUNDBOOK'),
                                                              ('service', 'SERVICE'),
                                                              ('technical_error', 'TECHNICALERROR')], default='service')

    # INVOICE
    type_of_invoice = fields.Selection(selection=[('C', 'CASH'), ('N', 'NONCASH')], default='C')
    type_of_self_iss = fields.Selection(selection=[('agreement', 'AGREEMENT'),
                                                   ('domestic', 'DOMESTIC'),
                                                   ('abroad', 'ABROAD'),
                                                   ('self', 'SELF'),
                                                   ('other', 'OTHER')], default=None)
    is_simplified_invoice = fields.Selection(string="Is simplified invoice?",
                                             selection=[('true', 'true'), ('false', 'false')],
                                             default='true')
    invoice_number = fields.Char("Invoice Order Number", copy=False)
    invoice_order_number = fields.Char("Order Number", copy=False)
    invoice_tax_free_amount = fields.Float(digits=(12, 2))  # optional
    invoice_markup_amount = fields.Float(digits=(12, 2))  # optional
    invoice_goods_exported_amount = fields.Float(digits=(12, 2))  # optional
    invoice_total_amount_without_vat = fields.Float(digits=(12, 2))  # compute
    invoice_total_amount = fields.Float(digits=(12, 2))
    invoice_total_price = fields.Float(digits=(12, 2))
    invoice_import_custom_declare_number = fields.Char("Numri i deklarates doganore te importit", size=50)
    iic_code = fields.Char("Kodi Identifikues i fatures (NSLF)", size=32, readonly=True, copy=False)
    iic_signature = fields.Char("Parametrat e Kodit Identifikues te fatures", size=512, copy=False)
    invoice_issue_date_time = fields.Char('Invoice Issue Date Time', copy=False)

    # CORRECTIVE INVOICE
    is_corrective_invoice = fields.Selection(string='Is corrective invoice?',
                                             selection=[('true', 'true'), ('false', 'false')],
                                             default='false')
    invoice_corrective_iic_ref = fields.Char('Kodi Identifikues i fatures qe po korigjohet', size=32, required=False)
    invoice_corrective_issue_date_time = fields.Char('Creation date and time of the invoice that is being corrected',
                                                     required=False)
    invoice_corrective_type = fields.Selection(selection=[('corrective', 'CORRECTIVE'),
                                                          ('debit', 'DEBIT'),
                                                          ('credit', 'CREDIT')], default='corrective', required=False)
    # INVOICE PAY METHODS

    pay_method_type = fields.Selection(selection=[('bank_note', 'BANKNOTE'),
                                                  ('card', 'CARD'),
                                                  ('check', 'CHECK'),
                                                  ('s_voucher', 'SVOUCHER'),
                                                  ('company', 'COMPANY'),
                                                  ('order', 'ORDER')], default='bank_note')
    pay_method_amount = fields.Float(digits=(12, 2))

    # INVOICE CURRENCY

    invoice_currency_code = fields.Char(related='pricelist_id.currency_id.name')
    # invoice_currency_exchange_rate = fields.Float(digits=(12, 3))  # related='pricelist_id.currency_id.inverse_rate'
    invoice_currency_is_buying = fields.Selection(selection=[('true', 'true'), ('false', 'false')], default='false')

    # INVOICE SELLER

    invoice_seller_id_number = fields.Char(related='company_id.vat', size=20)
    invoice_seller_id_type = fields.Selection(selection=[('nuis', 'NUIS'),
                                                         ('id', 'ID'),
                                                         ('pass', 'PASS'),
                                                         ('vat', 'VAT'),
                                                         ('tax', 'TAX'),
                                                         ('soc', 'SOC')], default='nuis')
    invoice_seller_id_name = fields.Char(related='company_id.name', size=100)
    invoice_seller_id_address = fields.Char(related='company_id.street', size=200)
    invoice_seller_id_city = fields.Char(related='company_id.city', size=100)
    invoice_seller_id_country = fields.Char(related='company_id.country_id.code')

    # INVOICE BUYER

    invoice_buyer_id_number = fields.Char(related='partner_id.vat', size=20)
    # invoice_buyer_id_type = fields.Selection(selection=[('nuis', 'NUIS'),
    #                                                     ('id', 'ID'),
    #                                                     ('pass', 'PASS'),
    #                                                     ('vat', 'VAT'),
    #                                                     ('tax', 'TAX'),
    #                                                     ('soc', 'SOC')], default=False)
    invoice_buyer_id_type = fields.Selection(selection=[('NUIS', '[NUIS] NUIS number'),
                                                        ('ID', '[ID] Personal ID number'),
                                                        ('PASS', '[PASS] Passport number'),
                                                        ('VAT', '[VAT] VAT number'),
                                                        ('TAX', '[TAX] TAX number'),
                                                        ('SOC', '[SOC] Social security number')], string="VAT Type",
                                             related="partner_id.vat_type")

    invoice_buyer_id_name = fields.Char(related='partner_id.name', size=100)
    invoice_buyer_id_address = fields.Char(related='partner_id.street', size=200)
    invoice_buyer_id_city = fields.Char(related='partner_id.city', size=100)
    invoice_buyer_id_country = fields.Char(related='partner_id.country_id.code')

    # INVOICE SAME TAXES

    invoice_same_tax_number_of_items = fields.Integer()  # to be computed
    invoice_same_tax_price_before_vat = fields.Float(digits=(12, 2))
    invoice_same_tax_vat_rate = fields.Float(digits=(12, 2))
    invoice_same_tax_type_of_exempt_from_vat = fields.Selection(selection=[('type_1', 'TYPE_1'),
                                                                           ('type_2', 'TYPE_2')],
                                                                default='type_1')
    invoice_same_tax_vat_amount = fields.Float(digits=(12, 2))

    xml = fields.Char(help='Generated XML for the fiscalization process', copy=False)
    qr_code = fields.Binary("QR Code", attachment=True, copy=False)
    iic_input = fields.Char(help='IIC input used for multiple purposes', copy=False)
    fic = fields.Char("Kodi Unik i fatures se fiskalizuar (NIVF)", readonly=True, copy=False)
    is_fiscalized = fields.Boolean(default=False, readonly=True, copy=False)
    fiscalization_error = fields.Char(copy=False,
                                      help='The error message received received when an invoice is not being fiscalized properly',
                                      default=None,
                                      readonly=True)

    business_unit_code = fields.Char("Business Unit Code", related="config_id.business_unit_code")
    operator_code = fields.Char("Operator Code", related="create_uid.operator_code")
    fiscalization_url = fields.Char("Fiscalization EndPoint", related="company_id.invoice_check_endpoint")
    ord_num = fields.Char(copy=False)
    fiscalization_time = fields.Datetime(copy=False)
    fiscalization_tries = fields.Integer(default=0)
    transporter_id = fields.Many2one("res.partner")
    license_plate_no = fields.Char()
    delivery_datetime = fields.Datetime()
    push_datetime = fields.Datetime(default=fields.Datetime.now(), copy=False)

    @api.model
    def _order_fields(self, ui_order):
        print("ui_order", ui_order)
        fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('iic_code'):
            # iic_code = self.search([('iic_code', '=', ui_order.get('iic_code'))])
            # if not iic_code:
            print("ui_order.get('iic_code')", ui_order.get('iic_code'))
            fields['iic_code'] = ui_order.get('iic_code', 0)
        fields["transporter_id"] = ui_order.get("transporter")
        fields["license_plate_no"] = ui_order.get("license")
        delivery_time = ui_order.get("delivery_datetime")
        if delivery_time:
            delivery_time = delivery_time.replace("T", " ")
            fields["delivery_datetime"] = delivery_time
        fields["push_datetime"] = ui_order.get("push_datetime")
        return fields

    @api.model
    def _process_order(self, order, draft, existing_order):
        pos_order = super(PosOrder, self)._process_order(order, draft, existing_order)
        if pos_order:
            order_id = self.browse(pos_order)
            if order_id.to_invoice and order_id.state == 'invoiced' and order_id.account_move:
                order_id.account_move.transporter_id = order_id.transporter_id.id or False
                order_id.account_move.license_plate_no = order_id.license_plate_no
                order_id.account_move.delivery_datetime = order_id.delivery_datetime
        return pos_order

    #
    # @api.model
    # def create_from_ui(self, orders):
    #     print("111111111create_from_uicreate_from_uicreate_from_ui", orders)
    #     # 2/0
    # #     print("!111111",self._context)
    # #     # 2 / 0
    # #     # for order in self.sudo().browse([o['id'] for o in order_ids]):
    # #     #     print("1111111111111",order)
    # #     # if order.loyalty_points != 0 and order.partner_id:
    # #     #     order.partner_id.loyalty_points += order.loyalty_points
    #     return super(PosOrder, self).create_from_ui(orders)

    # @api.model
    # def create_x(self, vals):
    #     res = super(PosOrder, self).create_x(vals)
    #     session_obj = self.env['pos.session'].sudo()
    #     session_id = False
    #     if vals.get('session_id'):
    #         session_id = session_obj.browse(int(vals.get('session_id')))
    #     if not session_id.config_id.disable_fiscalization:
    #
    #         # if session_id.config_id:
    #         tcr_code = session_id.config_id.tcr_code
    #
    #         # INVOICE
    #         res['invoice_order_number'] = session_id.config_id.sequence_id.get_next_without_consume() - 1
    #         # res['invoice_order_number'] = self.env['ir.sequence'].next_by_code(
    #         #     'pos.order.sequence.number')
    #         res['invoice_number'] = res['invoice_order_number'] + '/' + str(
    #             datetime.now().astimezone().replace(
    #                 microsecond=0).year) + '/' + tcr_code
    #         # HEADER
    #         res['header_UUID'] = uuid.uuid4()
    #         res['header_send_datetime'] = datetime.utcnow().replace(
    #             tzinfo=from_zone).astimezone(to_zone).replace(
    #             microsecond=0).isoformat()
    #
    #         company_id = self.env.user.company_id
    #         invoice_issuer_nuis = company_id.vat
    #         # invoice_busin_unit_code = company_id.business_unit_code
    #         invoice_busin_unit_code = None
    #         if session_id.config_id.allow_operating_unit:
    #             invoice_busin_unit_code = session_id.config_id.operating_unit_id.business_unit_code
    #         if not invoice_busin_unit_code:
    #             raise UserError("Provide Business Unit Code for the operating unit!")
    #         invoice_soft_code = company_id.software_code
    #         operator_code = res.user_id.operator_code
    #         if not operator_code:
    #             raise UserError("Provide Operator Code for the salesperson!")
    #
    #         # tcr_code = 'vc813ms173'
    #         # if self.config_id.tcr_code:
    #         # tcr_code = self.config_id.tcr_code
    #
    #         temp_dict = {'issuer_nuis': invoice_issuer_nuis, "busin_unit_code": invoice_busin_unit_code,
    #                      "tcr_code": tcr_code,
    #                      "soft_code": invoice_soft_code, "operator_code": operator_code}
    #
    #         # temp_dict = {'issuer_nuis': 'L62316009V',
    #         #              "busin_unit_code": "ll996sf167", "tcr_code": "vc813ms173",
    #         #              "soft_code": "bi558ej110", "operator_code": "pb999gp965"}
    #         coff = 1
    #         tax_free_amount = 0
    #         for line in res['lines']:
    #             if not line.tax_ids_after_fiscal_position:
    #                 tax_free_amount += line.price_subtotal_incl
    #         temp_dict['invoice_tax_free_amount'] = str("{:.2f}".format(tax_free_amount * coff))
    #
    #         temp_dict['type_of_invoice'] = dict(self._fields['type_of_invoice'].selection).get(res['type_of_invoice'])
    #         temp_dict['type_of_self_iss'] = dict(self._fields['type_of_self_iss'].selection).get(
    #             res['type_of_self_iss'])
    #         temp_dict['pay_method_type'] = dict(self._fields['pay_method_type'].selection).get(res['pay_method_type'])
    #         res['invoice_issue_date_time'] = temp_dict['invoice_issue_date_time'] = datetime.utcnow().replace(
    #             tzinfo=from_zone).astimezone(to_zone).replace(
    #             microsecond=0).isoformat()
    #         temp_dict['invoice_seller_id_type'] = dict(self._fields['invoice_seller_id_type'].selection).get(
    #             res['invoice_seller_id_type'])
    #         temp_dict['invoice_buyer_id_type'] = dict(self._fields['invoice_buyer_id_type'].selection).get(
    #             res['invoice_buyer_id_type'])
    #
    #         temp_dict['invoice_same_tax_type_of_exempt_from_vat'] = dict(
    #             self._fields['invoice_same_tax_type_of_exempt_from_vat'].selection).get(
    #             res['invoice_same_tax_type_of_exempt_from_vat'])
    #
    #         temp_dict['invoice_order_number'] = res['invoice_order_number']
    #         temp_dict['invoice_number'] = res['invoice_order_number'] + '/' + str(
    #             datetime.now().astimezone().replace(
    #                 microsecond=0).year) + '/' + tcr_code
    #         temp_dict['company_id_is_in_vat'] = company_id.company_id_is_in_vat
    #         temp_dict['invoice_total_amount_without_vat'] = str(
    #             "{:.2f}".format(float(sum([line['price_subtotal'] for line in res['lines']]))))
    #         temp_dict['is_reverse_charge'] = 'false'
    #
    #         temp_dict['pay_method_amount'] = str("{:.2f}".format(float(res['amount_paid'])))
    #
    #         temp_dict['vat_amt'] = str("{:.2f}".format(
    #             float(sum([line['price_subtotal_incl'] - line['price_subtotal'] for line in res['lines']]))))
    #
    #         # temp_dict['invoice_same_tax_number_of_items'] = str(len(set([getattr(line, 'tax_id', 0) for line in res['lines'] if getattr(line, 'tax_id', 0) != 0])))
    #         temp_dict['invoice_same_tax_price_before_vat'] = temp_dict['invoice_total_amount_without_vat']
    #         temp_dict['invoice_same_tax_vat_amount'] = temp_dict['vat_amt']
    #         # temp_dict['invoice_same_tax_vat_rate'] = str("{:.2f}".format(float(res['company_id']['vat_rate'])))
    #         temp_dict['invoice_same_tax_vat_rate'] = str("{:.2f}".format(float(0)))
    #
    #         temp_dict['exrate'] = '123.50'
    #         temp_dict['invoice_seller_id_country'] = 'ALB'
    #         temp_dict['invoice_buyer_id_country'] = 'ALB'
    #         temp_dict['invoice_seller_id_number'] = temp_dict['issuer_nuis']
    #
    #         temp_dict['is_simplified_invoice'] = session_id.config_id.is_simplify_inv
    #
    #         # For Summary invoice
    #
    #         # if session_id.config_id.module_pos_restaurant:
    #         #     kitchen_order_ids = self.env["pos.kitchen.order"].search([("pos_reference", "=", res.pos_reference)])
    #         #     if kitchen_order_ids:
    #         #         iics = kitchen_order_ids.mapped("iic_code")
    #         #         print("iics", iics)
    #         #         sum_inv_iic_refs = []
    #         #         for k_order in kitchen_order_ids:
    #         #             k_order.pos_order_id = res.id
    #         #             sum_inv_iic_refs.append({
    #         #                 "IIC": k_order.iic_code,
    #         #                 "IssueDateTime": k_order.date_order.utcnow().replace(tzinfo=from_zone).astimezone(
    #         #                     to_zone).replace(microsecond=0).isoformat(),
    #         #             })
    #         #         temp_dict['sum_inv_iic_refs'] = sum_inv_iic_refs
    #
    #         vals_dict = {field: getattr(res, field, None) for field in dir(res)}
    #
    #         if res['amount_total'] < 0:
    #             pos_reference = res['pos_reference']
    #             pos_order = self.env['pos.order'].search(
    #                 ['|', ("pos_reference", "=", pos_reference), ("id", "=", res.returned_order_id.id),
    #                  ("amount_total", ">", 0)],
    #                 limit=1)
    #             # if res['return_ref'] and not pos_order:
    #             #     pos_order = self.env['pos.order'].search(
    #             #         [("pos_reference", "=", res['return_ref']), ("amount_total", ">", 0)],
    #             #         limit=1)
    #             # 2/0
    #             # if pos_order.returned_order_id:
    #             #     iic_code = pos_order.returned_order_id.iic_code
    #             #     invoice_issue_date_time = pos_order.returned_order_id.invoice_issue_date_time
    #             # else:
    #
    #             if pos_order:
    #                 iic_code = pos_order.iic_code
    #                 invoice_issue_date_time = pos_order.invoice_issue_date_time
    #                 if iic_code and invoice_issue_date_time:
    #                     res['is_corrective_invoice'] = 'true'
    #                     res['invoice_corrective_iic_ref'] = iic_code
    #                     res['invoice_corrective_issue_date_time'] = invoice_issue_date_time
    #                     res['invoice_corrective_type'] = 'credit'
    #
    #         vals_dict.update(temp_dict)
    #         vals.update(vals_dict)
    #
    #         company_p12_certificate = company_id.p12_certificate.datas
    #         if company_p12_certificate:
    #             company_p12_certificate = base64.b64decode(company_p12_certificate)
    #             certificate_password = company_id.certificate_password.encode('utf-8')
    #
    #         res['xml'], res['iic_input'], res['iic_code'], res['iic_signature'] = make_invoice(data=vals,
    #                                                                                            company_p12_certificate=company_p12_certificate,
    #                                                                                            certificate_password=certificate_password)
    #         print("PAYLOAD ----->", res['xml'])
    #         inv_check_api_endpoint = company_id.invoice_check_endpoint
    #
    #         res['qr_code'] = make_invoice_qr_code(inv_check_api_endpoint=inv_check_api_endpoint,
    #                                               invoice_iic=res['iic_code'],
    #                                               invoice_issuer_nuis=vals_dict['issuer_nuis'],
    #                                               invoice_issue_date_time=vals_dict['invoice_issue_date_time'],
    #                                               invoice_inv_ord_num=vals_dict['invoice_order_number'],
    #                                               invoice_busin_unit_code=vals_dict['busin_unit_code'],
    #                                               invoice_tcr_code=vals_dict['tcr_code'],
    #                                               invoice_soft_code=vals_dict['soft_code'],
    #                                               invoice_tot_price=str(
    #                                                   "{:.2f}".format(float(vals_dict['amount_total'])))
    #                                               )
    #
    #         response_parsed = ''
    #         try:
    #             url = company_id.fiscalization_endpoint
    #             response = make_http_call(res['xml'], url)
    #             print("RESPONSE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", response)
    #             response_parsed = parse_response(response)
    #         except Exception as e:
    #             print("11111111", e)
    #
    #         if response_parsed and not isinstance(response_parsed, dict):
    #             res['fic'] = response_parsed
    #             res['is_fiscalized'] = True
    #             res['fiscalization_error'] = None
    #         if isinstance(response_parsed, dict):
    #             res['fic'] = None
    #             res['is_fiscalized'] = False
    #             res['fiscalization_error'] = response_parsed['Error']
    #     return res

    # @api.multi
    # def write(self, vals):
    #     res = super(PosOrder, self).write(vals)
    #     if vals.get('state') == 'paid' and not self.is_fiscalized:
    #         self.fiscalize()
    #     return res

    @api.model
    def create(self, vals_list):
        print("vals_list", vals_list)
        res = super(PosOrder, self).create(vals_list)

        ord_num = res.config_id.sequence_id.get_next_without_consume()
        res.ord_num = ord_num
        return res

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        print("order_ids ", order_ids)
        if order_ids:
            order_ids_map = map(lambda i: i["id"], order_ids)
            order_ids_ls = list(order_ids_map)
            order_obj_ids = self.search([("id", "in", order_ids_ls)])
            for order_id in order_obj_ids:

                if len(order_ids) == 1 and not order_id.is_fiscalized:
                    order_id.fiscalize()
        return order_ids

    def fiscalize(self):
        if not self.config_id.disable_fiscalization:
            tcr_code = self.config_id.tcr_code

            # INVOICE
            res = self
            # TODO When submitting after create it is taking it again from ir sequence.

            # res['invoice_order_number'] = self.config_id.sequence_id.get_next_without_consume() - 1
            res['invoice_order_number'] = self.ord_num
            if not self.ord_num:
                res['invoice_order_number'] = self.config_id.sequence_id.get_next_without_consume()

            res['invoice_number'] = res['invoice_order_number'] + '/' + str(
                datetime.now().astimezone().replace(
                    microsecond=0).year) + '/' + tcr_code
            # HEADER
            res['header_UUID'] = uuid.uuid4()
            res['header_send_datetime'] = datetime.utcnow().replace(
                tzinfo=from_zone).astimezone(to_zone).replace(
                microsecond=0).isoformat()

            company_id = self.env.user.company_id
            invoice_issuer_nuis = company_id.vat
            # invoice_busin_unit_code = company_id.business_unit_code
            invoice_busin_unit_code = None
            if self.config_id.allow_operating_unit:
                invoice_busin_unit_code = self.config_id.operating_unit_id.business_unit_code
            if not invoice_busin_unit_code:
                raise UserError("Provide Business Unit Code for the operating unit!")
            invoice_soft_code = company_id.software_code
            operator_code = res.user_id.operator_code
            if not operator_code:
                raise UserError("Provide Operator Code for the salesperson!")

            temp_dict = {'issuer_nuis': invoice_issuer_nuis, "busin_unit_code": invoice_busin_unit_code,
                         "tcr_code": tcr_code,
                         "soft_code": invoice_soft_code, "operator_code": operator_code}

            coff = 1
            tax_free_amount = 0
            if not company_id.company_id_is_in_vat:
                for line in res['lines']:
                    if not line.tax_ids_after_fiscal_position:
                        tax_free_amount += line.price_subtotal_incl
            temp_dict['invoice_tax_free_amount'] = str("{:.2f}".format(tax_free_amount * coff))

            temp_dict['type_of_invoice'] = dict(self._fields['type_of_invoice'].selection).get(res['type_of_invoice'])
            temp_dict['type_of_self_iss'] = dict(self._fields['type_of_self_iss'].selection).get(
                res['type_of_self_iss'])
            temp_dict['pay_method_type'] = dict(self._fields['pay_method_type'].selection).get(res['pay_method_type'])
            # current_datetime_iso = datetime.utcnow().replace(tzinfo=from_zone).astimezone(to_zone).replace(
            #     microsecond=0).isoformat()
            order_create_datetime_iso = res.push_datetime.replace(tzinfo=from_zone).astimezone(to_zone).replace(
                microsecond=0).isoformat()

            time_difference = (datetime.now() - res.push_datetime).total_seconds() / 60.0
            res['invoice_issue_date_time'] = temp_dict['invoice_issue_date_time'] = order_create_datetime_iso
            if time_difference <= 2:
                temp_dict["online"] = True
                res['header_send_datetime'] = res['invoice_issue_date_time']
            else:
                temp_dict["online"] = False

            # res['invoice_issue_date_time'] = temp_dict['invoice_issue_date_time'] = datetime.utcnow().replace(
            #     tzinfo=from_zone).astimezone(to_zone).replace(
            #     microsecond=0).isoformat()
            temp_dict['invoice_seller_id_type'] = dict(self._fields['invoice_seller_id_type'].selection).get(
                res['invoice_seller_id_type'])
            # temp_dict['invoice_buyer_id_type'] = dict(self._fields['invoice_buyer_id_type'].selection).get(
            #     res['invoice_buyer_id_type'])
            temp_dict['invoice_buyer_id_type'] = res['invoice_buyer_id_type']

            temp_dict['invoice_same_tax_type_of_exempt_from_vat'] = dict(
                self._fields['invoice_same_tax_type_of_exempt_from_vat'].selection).get(
                res['invoice_same_tax_type_of_exempt_from_vat'])

            temp_dict['invoice_order_number'] = res['invoice_order_number']
            temp_dict['invoice_number'] = res['invoice_order_number'] + '/' + str(
                datetime.now().astimezone().replace(
                    microsecond=0).year) + '/' + tcr_code
            temp_dict['company_id_is_in_vat'] = company_id.company_id_is_in_vat
            temp_dict['invoice_total_amount_without_vat'] = str(
                "{:.2f}".format(float(sum([line['price_subtotal'] for line in res['lines']]))))
            print("ccccccccccccc", temp_dict['invoice_total_amount_without_vat'])
            temp_dict['is_reverse_charge'] = 'false'

            temp_dict['pay_method_amount'] = str("{:.2f}".format(float(res['amount_paid'])))

            temp_dict['vat_amt'] = str("{:.2f}".format(
                float(sum([line['price_subtotal_incl'] - line['price_subtotal'] for line in res['lines']]))))

            # temp_dict['invoice_same_tax_number_of_items'] = str(len(set([getattr(line, 'tax_id', 0) for line in res['lines'] if getattr(line, 'tax_id', 0) != 0])))
            temp_dict['invoice_same_tax_price_before_vat'] = temp_dict['invoice_total_amount_without_vat']
            temp_dict['invoice_same_tax_vat_amount'] = temp_dict['vat_amt']
            # temp_dict['invoice_same_tax_vat_rate'] = str("{:.2f}".format(float(res['company_id']['vat_rate'])))
            temp_dict['invoice_same_tax_vat_rate'] = str("{:.2f}".format(float(0)))

            temp_dict['exrate'] = '123.50'
            temp_dict['invoice_seller_id_country'] = 'ALB'
            temp_dict['invoice_buyer_id_country'] = 'ALB'
            temp_dict['invoice_seller_id_number'] = temp_dict['issuer_nuis']

            temp_dict['is_simplified_invoice'] = self.config_id.is_simplify_inv

            # For Summary invoice

            # if session_id.config_id.module_pos_restaurant:
            #     kitchen_order_ids = self.env["pos.kitchen.order"].search([("pos_reference", "=", res.pos_reference)])
            #     if kitchen_order_ids:
            #         iics = kitchen_order_ids.mapped("iic_code")
            #         print("iics", iics)
            #         sum_inv_iic_refs = []
            #         for k_order in kitchen_order_ids:
            #             k_order.pos_order_id = res.id
            #             sum_inv_iic_refs.append({
            #                 "IIC": k_order.iic_code,
            #                 "IssueDateTime": k_order.date_order.utcnow().replace(tzinfo=from_zone).astimezone(
            #                     to_zone).replace(microsecond=0).isoformat(),
            #             })
            #         temp_dict['sum_inv_iic_refs'] = sum_inv_iic_refs

            # vals_dict = {field: getattr(res, field, None) for field in dir(res)}

            # pos_reference = res['pos_reference']
            # pos_order = self.env['pos.order'].search(
            #     ['|', ("pos_reference", "=", pos_reference), ("id", "=", res.refunded_order_ids.id),
            #      ("amount_total", ">", 0)],
            #     limit=1)
            # if res['return_ref'] and not pos_order:
            #     pos_order = self.env['pos.order'].search(
            #         [("pos_reference", "=", res['return_ref']), ("amount_total", ">", 0)],
            #         limit=1)
            # 2/0
            # if pos_order.returned_order_id:
            #     iic_code = pos_order.returned_order_id.iic_code
            #     invoice_issue_date_time = pos_order.returned_order_id.invoice_issue_date_time
            # else:
            if res['amount_total'] < 0 and res.refunded_order_ids:

                pos_order = res.refunded_order_ids[0]
                if pos_order:
                    iic_code = pos_order.iic_code
                    invoice_issue_date_time = pos_order.invoice_issue_date_time
                    if iic_code and invoice_issue_date_time:
                        res['is_corrective_invoice'] = 'true'
                        res['invoice_corrective_iic_ref'] = iic_code
                        res['invoice_corrective_issue_date_time'] = invoice_issue_date_time
                        res['invoice_corrective_type'] = 'credit'

            # vals_dict.update(temp_dict)
            # res.update(vals_dict)

            vals_dict = {field: getattr(self, field, None) for field in dir(self)}

            vals_dict.update(temp_dict)

            company_p12_certificate = company_id.p12_certificate
            if company_p12_certificate:
                company_p12_certificate = base64.b64decode(company_p12_certificate)
                certificate_password = company_id.certificate_password.encode('utf-8')

            res['xml'], res['iic_input'], res['iic_code'], res['iic_signature'] = make_invoice(data=vals_dict,
                                                                                               company_p12_certificate=company_p12_certificate,
                                                                                               certificate_password=certificate_password)
            print("PAYLOAD ----->", res['xml'])
            # _logger.info("PAYLOAD -----> \n\n%s" % res["xml"])
            inv_check_api_endpoint = company_id.invoice_check_endpoint

            res['qr_code'] = make_invoice_qr_code(inv_check_api_endpoint=inv_check_api_endpoint,
                                                  invoice_iic=res['iic_code'],
                                                  invoice_issuer_nuis=vals_dict['issuer_nuis'],
                                                  invoice_issue_date_time=vals_dict['invoice_issue_date_time'],
                                                  invoice_inv_ord_num=vals_dict['invoice_order_number'],
                                                  invoice_busin_unit_code=vals_dict['busin_unit_code'],
                                                  invoice_tcr_code=vals_dict['tcr_code'],
                                                  invoice_soft_code=vals_dict['soft_code'],
                                                  invoice_tot_price=str(
                                                      "{:.2f}".format(float(vals_dict['amount_total'])))
                                                  )

            response_parsed = ''
            try:
                url = company_id.fiscalization_endpoint
                response = make_http_call(res['xml'], url, timeout=7.5)
                print("RESPONSE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", response)
                # _logger.info("RESPONSE -----> \n\n%s" % response)
                response_parsed = parse_response(response)
            except requests.Timeout as e:
                _logger.error("Timeout: %s" % e)
                print("Timeout", e)
            except requests.exceptions.RequestException as e:
                _logger.error("RequestException: %s" % e)
                print("11111111", e)
            except Exception as e:
                _logger.error("\n\n There is some unexpected error, halt and check: %s \n\n" % e)
            finally:
                res["fiscalization_tries"] += 1
                print("?????????????????????????@@@@", res.fiscalization_tries)
            if response_parsed and not isinstance(response_parsed, dict):
                res['fic'] = response_parsed
                res['is_fiscalized'] = True
                res['fiscalization_time'] = datetime.now()
                res['fiscalization_error'] = None
            if isinstance(response_parsed, dict):
                res['fic'] = None
                res['is_fiscalized'] = False
                res['fiscalization_error'] = response_parsed['Error']

        # ******************* OLD Implementation ********************
        # self.ensure_one()
        # self['header_UUID'] = uuid.uuid4()
        # self['header_send_datetime'] = datetime.utcnow().replace(
        #     tzinfo=from_zone).astimezone(to_zone).replace(
        #     microsecond=0).isoformat()
        # if not self.config_id.disable_fiscalization:
        #     company_id = self.env.user.company_id
        #     invoice_issuer_nuis = company_id.vat
        #     invoice_busin_unit_code = None
        #     if self.config_id.allow_operating_unit:
        #         invoice_busin_unit_code = self.config_id.operating_unit_id.business_unit_code
        #     if not invoice_busin_unit_code:
        #         raise UserError("Provide Business Unit Code for the operating unit!")
        #     # invoice_busin_unit_code = company_id.business_unit_code
        #     invoice_soft_code = company_id.software_code
        #     operator_code = self.user_id.operator_code
        #
        #     tcr_code = self.config_id.tcr_code
        #
        #     self['invoice_number'] = self['invoice_order_number'] + '/' + str(
        #         datetime.now().astimezone().replace(
        #             microsecond=0).year) + '/' + tcr_code
        #
        #     if not operator_code:
        #         raise UserError("Provide Operator Code for the salesperson!")
        #
        #     # temp_dict = {'issuer_nuis': 'L62316009V',
        #     #              "busin_unit_code": "ll996sf167", "tcr_code": "vc813ms173",
        #     #              "soft_code": "bi558ej110", "operator_code": "pb999gp965"}
        #     temp_dict = {'issuer_nuis': invoice_issuer_nuis, "busin_unit_code": invoice_busin_unit_code,
        #                  "tcr_code": tcr_code,
        #                  "soft_code": invoice_soft_code, "operator_code": operator_code}
        #
        #     temp_dict['type_of_invoice'] = dict(
        #         self._fields['type_of_invoice'].selection).get(
        #         self['type_of_invoice'])
        #     temp_dict['type_of_self_iss'] = dict(
        #         self._fields['type_of_self_iss'].selection).get(
        #         self['type_of_self_iss'])
        #     temp_dict['pay_method_type'] = dict(
        #         self._fields['pay_method_type'].selection).get(
        #         self['pay_method_type'])
        #
        #     temp_dict['invoice_seller_id_type'] = dict(
        #         self._fields['invoice_seller_id_type'].selection).get(
        #         self['invoice_seller_id_type'])
        #
        #     tax_free_amount = 0
        #     coff = 1
        #     for line in self['lines']:
        #         if not line.tax_ids_after_fiscal_position:
        #             tax_free_amount += line.price_subtotal_incl
        #     temp_dict['invoice_tax_free_amount'] = str("{:.2f}".format(tax_free_amount * coff))
        #
        #     temp_dict['invoice_same_tax_type_of_exempt_from_vat'] = dict(
        #         self._fields[
        #             'invoice_same_tax_type_of_exempt_from_vat'].selection).get(
        #         self['invoice_same_tax_type_of_exempt_from_vat'])
        #
        #     temp_dict['invoice_order_number'] = self['invoice_order_number']
        #     temp_dict['invoice_number'] = self['invoice_number']
        #     temp_dict['company_id_is_in_vat'] = company_id.company_id_is_in_vat
        #     temp_dict['is_simplified_invoice'] = self.config_id.is_simplify_inv
        #
        #     temp_dict['invoice_total_amount_without_vat'] = str("{:.2f}".format(
        #         float(sum([line['price_subtotal'] for line in self['lines']]))))
        #     temp_dict['is_reverse_charge'] = 'false'
        #     temp_dict['pay_method_amount'] = str(
        #         "{:.2f}".format(float(self['amount_paid'])))
        #
        #     temp_dict['vat_amt'] = str("{:.2f}".format(float(
        #         sum([line['price_subtotal_incl'] - line['price_subtotal'] for line
        #              in self['lines']]))))
        #
        #     temp_dict['invoice_same_tax_price_before_vat'] = temp_dict[
        #         'invoice_total_amount_without_vat']
        #     temp_dict['invoice_same_tax_vat_amount'] = temp_dict['vat_amt']
        #     temp_dict['invoice_same_tax_vat_rate'] = str(
        #         "{:.2f}".format(float(0)))
        #
        #     temp_dict['exrate'] = '123.50'
        #     temp_dict['invoice_seller_id_country'] = 'ALB'
        #     temp_dict['invoice_buyer_id_country'] = 'ALB'
        #     temp_dict['invoice_seller_id_number'] = temp_dict['issuer_nuis']
        #
        #     # only for invoices that are not sent immediately (manual fiscalization)
        #     temp_dict['header_subseq_delivery_type'] = 'NOINTERNET'
        #     temp_dict['iic_code'] = False
        #     if self.iic_code:
        #         temp_dict['iic_code'] = self.iic_code
        #
        #     vals_dict = {field: getattr(self, field, None) for field in dir(self)}
        #
        #     vals_dict.update(temp_dict)
        #
        #     company_p12_certificate = company_id.p12_certificate.datas
        #     company_p12_certificate = base64.b64decode(company_p12_certificate)
        #     certificate_password = company_id.certificate_password.encode('utf-8')
        #
        #     self['xml'], self['iic_input'], self['iic_code'], self[
        #         'iic_signature'] = make_invoice(data=vals_dict, company_p12_certificate=company_p12_certificate,
        #                                         certificate_password=certificate_password)
        #     # print("qqqqqqqqq222222222222222222222222222", self['xml'])
        #     inv_check_api_endpoint = company_id.invoice_check_endpoint
        #
        #     self['qr_code'] = make_invoice_qr_code(inv_check_api_endpoint=inv_check_api_endpoint,
        #                                            invoice_iic=self['iic_code'],
        #                                            invoice_issuer_nuis=vals_dict['issuer_nuis'],
        #                                            invoice_issue_date_time=vals_dict['invoice_issue_date_time'],
        #                                            invoice_inv_ord_num=vals_dict['invoice_order_number'],
        #                                            invoice_busin_unit_code=vals_dict['busin_unit_code'],
        #                                            invoice_tcr_code=vals_dict['tcr_code'],
        #                                            invoice_soft_code=vals_dict['soft_code'],
        #                                            invoice_tot_price=str(
        #                                                "{:.2f}".format(float(vals_dict['amount_total'])))
        #                                            )
        #     response_parsed = ''
        #     try:
        #         url = company_id.fiscalization_endpoint
        #         response = make_http_call(self['xml'], url)
        #         response_parsed = parse_response(response)
        #     except Exception as e:
        #         print("11111111", e)
        #     # print("xddddddddddddddddd", response_parsed)
        #     if response_parsed and not isinstance(response_parsed, dict):
        #         self['fic'] = response_parsed
        #         self['is_fiscalized'] = True
        #         self['fiscalization_error'] = None
        #     if isinstance(response_parsed, dict):
        #         self['fic'] = None
        #         self['is_fiscalized'] = False
        #         self['fiscalization_error'] = response_parsed['Error']
        # return self

    def pos_order_bulk_fiscalization(self):
        # print("SELF", self)
        non_fiscalized_order_ids = self.filtered(lambda order: not order.is_fiscalized)
        # print("non_fiscalized_order_ids", non_fiscalized_order_ids)
        for order_id in non_fiscalized_order_ids:
            order_id.fiscalize()

    def pos_order_bulk_fiscalization_cron_job(self):
        # print("SELF", self)
        today = fields.Datetime.now()
        last_month = today - timedelta(days=30)
        non_fiscalized_order_ids = self.env["pos.order"].search(
            [("is_fiscalized", "=", False), ('date_order', '>=', last_month), '|', ('fiscalization_tries', "<", 5),
             ('fiscalization_tries', "=", False)])
        # non_fiscalized_order_ids = self.filtered(lambda order: not order.is_fiscalized)
        # print("non_fiscalized_order_ids", non_fiscalized_order_ids)
        for order_id in non_fiscalized_order_ids:
            order_id.fiscalize()

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        # print("order", order.iic_code)
        res.update({
            # Added fields for fiscalization
            'nslf': order.iic_code,
            'nivf': order.fic,
            'amount_total_formatted': str("{:.2f}".format(order.amount_total)),
            'business_unit_code': order.config_id.business_unit_code,
            'operator_code': order.operator_code,
            'fiscalization_url': order.fiscalization_url,
            'invoice_issue_date_time': order.invoice_issue_date_time,
            'business_unit_address': order.config_id.operating_unit_id.partner_id._display_address(
                without_company=True),
            'partner_name': order.partner_id.name,
            'vat': order.partner_id.vat,
            'street': order.partner_id.street,
            'city': order.partner_id.city,
            'country_id': order.partner_id.country_id.name,
            'zip': order.partner_id.zip,
        })

        return res


class ConnectionTest(http.Controller):
    @http.route('/is-alive', type='http', auth='public')
    def download_document(self):
        return "alive"
