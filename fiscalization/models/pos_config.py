import datetime

from odoo import api, fields, models, exceptions
from odoo.exceptions import ValidationError
from ..services.tcr import make_tcr
from ..services.http_calls.response import parse_response
from ..services.http_calls.request import make_http_call
import uuid
import base64


class PosConfig(models.Model):
    _inherit = "pos.config"

    tcr_int_id = fields.Char("TCRIntId")
    tcr_type = fields.Selection(string="TCR type", selection=[('REGULAR', 'REGULAR'), ('VENDING', 'VENDING')],
                                default='REGULAR')
    tcr_code = fields.Char("TCR Code", size=10)
    disable_fiscalization = fields.Boolean("Disable Fiscalization")
    is_simplify_inv = fields.Boolean(string="IsSimplifiedInv")
    business_unit_code = fields.Char(related='operating_unit_id.business_unit_code')
    show_company_logo = fields.Boolean("Show Company Logo")
    enable_transporter = fields.Boolean()

    # image_check = fields.Binary(string="Image (jpg)")
    # image_size = fields.Integer("Image Size(bytes)")

    # ---- pos e-invoice default value fields ----
    # enable_e_invoice = fields.Boolean()
    # business_process = fields.Selection(
    #     [('P1', '[P1] Invoicing the supply of goods and services ordered on a contract basis'),
    #      ('P2', '[P2] Periodic invoicing of contract-based delivery'),
    #      ('P3', '[P3] Invoicing delivery over unforeseen orders'),
    #      ('P4', '[P4] Advance Payment'),
    #      ('P5', '[P5] Spot payment'),
    #      ('P6', '[P6] Payment before delivery on the based on a purchase order'),
    #      ('P7', '[P7] Invoices with reference to a dispatch note'),
    #      ('P8', '[P8] Invoices with reference to dispatch and receipt'),
    #      ('P9', '[P9] Approval or Negative Invoicing'),
    #      ('P10', '[P10] Corrective Invoicing'),
    #      ('P11', '[P11] Partial and final invoicing'),
    #      ], default="P1", required=True, )
    #
    # type_code = fields.Selection(
    #     [("80", "[80] Debit note related to goods or services"),
    #      ("82", "[82] Metered services invoice"),
    #      ("84", "[84] Debit note related to financial adjustments"),
    #      ("380", "[380] Commercial invoice"),
    #      ("383", "[383] Debit note"),
    #      ("384", "[384] Corrective invoice"),
    #      ("386", "[386] Prepayment invoice"),
    #      ("388", "[388] Tax invoice"),
    #      ("393", "[393] Factored invoice"),
    #      ("395", "[395] Consignment invoice"),
    #      ("575", "[575] Forwarder's invoice"),
    #      ("780", "[780] Freight invoice"),
    #      ("81", "[81] Credit note related to goods or services"),
    #      ("83", "[83] Credit note related to financial adjustments"),
    #      ("381", "[381] Credit note"),
    #      ("396", "[396] Factored credit note"),
    #      ("532", "[532] Forwarder's credit note"),
    #      ], default="388")

    # @api.onchange("enable_e_invoice")
    # def check_module_account(self):
    #     if not self.module_account and self.enable_e_invoice:
    #         raise ValidationError("Enable Invoicing to use POS E-Invoicing!")

    def generate_tcr_code(self):
        self.ensure_one()
        if not self['tcr_code']:
            issuer_nuis = self['company_id']['vat'] or 'L62316009V'
            busin_unit_code = self['operating_unit_id']['business_unit_code'] or 'll996sf167'
            soft_code = self['company_id']['software_code'] or 'bi558ej110'
            mantainer_code = self['company_id']['maintainer_code'] or 'ds402gh507'
            int_id = self['name'] or str(uuid.uuid4()).replace('-', '')[:10]
            valid_from = str(datetime.date.today())
            valid_to = str(datetime.date.today() + datetime.timedelta(days=365))
            tcr_type = self['tcr_type'] or 'REGULAR'
            data = {'IssuerNUIS': issuer_nuis,
                    'BusinUnitCode': busin_unit_code, 'TCRIntID': int_id,
                    'SoftCode': soft_code, 'MaintainerCode': mantainer_code,
                    'ValidFrom': valid_from, 'ValidTo': valid_to,
                    'Type': tcr_type}

            company_id = self.env.user.company_id

            company_p12_certificate = company_id.p12_certificate
            if company_p12_certificate:
                company_p12_certificate = base64.b64decode(company_p12_certificate)
                certificate_password = company_id.certificate_password.encode('utf-8')

            tcr_xml = make_tcr(data=data, company_p12_certificate=company_p12_certificate,
                               certificate_password=certificate_password)
            url = company_id.fiscalization_endpoint
            response = make_http_call(tcr_xml, url)
            response_parsed = parse_response(response)
            if response_parsed:
                if isinstance(response_parsed, dict):
                    raise exceptions.ValidationError(response_parsed['Error'])
                else:
                    self['tcr_code'] = response_parsed
            return True
        else:
            raise exceptions.ValidationError('TCR already exists!')


class PaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    create_e_invoice = fields.Boolean()