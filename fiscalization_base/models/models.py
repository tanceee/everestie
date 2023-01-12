# -*- coding: utf-8 -*-
import base64

from lxml import etree

from odoo import models, fields
from odoo.exceptions import ValidationError
from ..services.get_taxpayers import get_taxpayers_req_data
from odoo.addons.fiscalization_base.services.http_calls.request import make_http_call
import requests


class ResCompany(models.Model):
    _inherit = "res.company"

    software_code = fields.Char()
    maintainer_code = fields.Char()
    fiscalization_endpoint = fields.Char()
    einvoice_endpoint = fields.Char()
    invoice_check_endpoint = fields.Char()
    p12_certificate = fields.Binary()
    certificate_file_name = fields.Char()
    certificate_password = fields.Char()
    company_id_is_in_vat = fields.Boolean('Issuer is in VAT register')


class ResUsers(models.Model):
    _inherit = "res.users"

    operator_code = fields.Char()


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    business_unit_code = fields.Char()


class ResPartner(models.Model):
    _inherit = "res.partner"

    vat_type = fields.Selection(selection=[('NUIS', '[NUIS] NUIS number'),
                                           ('ID', '[ID] Personal ID number'),
                                           ('PASS', '[PASS] Passport number'),
                                           ('VAT', '[VAT] VAT number'),
                                           ('TAX', '[TAX] TAX number'),
                                           ('SOC', '[SOC] Social security number')], default="NUIS", string="VAT Type")
    is_transporter = fields.Boolean()
    license_plate_no = fields.Char()

    def get_tax_payer(self):
        if self.vat_type == "NUIS" and self.vat:
            company_id = self.env.user.company_id

            company_p12_certificate = company_id.p12_certificate
            company_p12_certificate = base64.b64decode(company_p12_certificate)
            certificate_password = company_id.certificate_password.encode('utf-8')
            request_xml_data = get_taxpayers_req_data(input_data=self.vat,
                                                      company_p12_certificate=company_p12_certificate,
                                                      certificate_password=certificate_password)
            print("XML", request_xml_data)

            try:
                url = company_id.einvoice_endpoint
                response = make_http_call(request_xml_data, url)
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                raise ValidationError(e)

            if response:
                print("Response", str(response))
                tin_found = False
                root = etree.fromstring(response)
                for taxpayers in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}Taxpayers'):
                    for element in taxpayers.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}Taxpayer'):
                        print("Taxpayer", element.get("Address"))
                        street = element.get("Address")
                        country_code = element.get("Country")
                        name = element.get("Name")
                        city = element.get("Town")
                        country_id = self.env["res.country"].search([("code_alpha3", "=", country_code)], limit=1).id
                        self.street = street
                        self.country_id = country_id
                        self.name = name
                        self.city = city
                        tin_found = True
                    if not tin_found:
                        raise ValidationError("Taxpayer Not Fount, Check the VAT number!")

                for faultcode in root.iter('faultcode'):
                    for faultstring in root.iter('faultstring'):
                        raise ValidationError(
                            "Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))
        else:
            if self.vat_type != "NUIS":
                raise ValidationError('VAT type must be "NUIS"')
            if not self.vat:
                raise ValidationError('Fill the VAT Number!')


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def get_next_without_consume(self):
        """ Returns the next number in the preferred sequence"""
        if not self.use_date_range:
            return self.number_next_actual
        # date mode
        dt = fields.Date.today()
        if self._context.get('ir_sequence_date'):
            dt = self._context.get('ir_sequence_date')
        seq_date = self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
        return seq_date.with_context(ir_sequence_date_range=seq_date.date_from).number_next_actual


class AccountTax(models.Model):
    _inherit = "account.tax"

    exempt_code = fields.Selection([("TYPE_1", "TYPE_1"), ("TYPE_2", "TYPE_2"), ("TAX_FREE", "TAX_FREE")],
                                   help="Values for the exempt from VAT types")
    description_exempt = fields.Text()
