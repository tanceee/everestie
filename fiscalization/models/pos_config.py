import datetime

from odoo import api, fields, models, exceptions
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
    disable_fiscalization = fields.Boolean("Discable Fiscalization")
    is_simplify_inv = fields.Boolean(string="IsSimplifiedInv")
    business_unit_code = fields.Char(related='operating_unit_id.business_unit_code')
    show_company_logo = fields.Boolean("Show Company Logo")
    enable_transporter = fields.Boolean()
    # image_check = fields.Binary(string="Image (jpg)")
    # image_size = fields.Integer("Image Size(bytes)")

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
