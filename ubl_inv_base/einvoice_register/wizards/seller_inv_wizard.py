import base64
import datetime
import requests

from lxml import etree
from pytz import timezone
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ..models import fetch_e_invoice, change_status
from dateutil import tz
from odoo.addons.fiscalization_base.services.http_calls.request import make_http_call


class SellerEInvoiceWizard(models.TransientModel):
    _name = "seller.einvoice.wizard"
    _rec_name = "start_datetime"

    start_datetime = fields.Datetime(required=True)
    end_datetime = fields.Datetime(required=True)
    inv_to_fetch = fields.Selection(
        [("ALL", "ALL"), ("DELIVERED", "DELIVERED"), ("ACCEPTED", "ACCEPTED"), ("REFUSED", "REFUSED")],
        default="DELIVERED", required=True)
    seller_einv_line_ids = fields.One2many("seller.einvoice.line.wizard", "einv_wizard_id")
    change_status_to = fields.Selection([("ACCEPTED", "ACCEPTED"), ("REFUSED", "REFUSED")])
    response = fields.Text(readonly=True)
    testing = fields.Char()

    def fetch_seller_einvoice(self):
        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')

        # from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Tirane')

        rec_from_datetime = self.start_datetime.astimezone(to_zone).replace(
            microsecond=0).isoformat()
        rec_to_datetime = self.end_datetime.astimezone(to_zone).replace(
            microsecond=0).isoformat()
        final_xml = fetch_e_invoice.fetch_e_invoice(company_p12_certificate=company_p12_certificate,
                                                    certificate_password=certificate_password,
                                                    rec_from_datetime=rec_from_datetime,
                                                    rec_to_datetime=rec_to_datetime)
        url = company_id.einvoice_endpoint
        try:
            response = make_http_call(final_xml, url)
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            # This is the correct syntax
            raise ValidationError(e)
        root = etree.fromstring(response)

        self.seller_einv_line_ids = False
        for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}Einvoice'):
            inv_status = element.get("Status")
            if self.inv_to_fetch != "ALL":
                if self.inv_to_fetch == inv_status:
                    pass
                else:
                    continue
            due_datetime = element.get("DueDateTime")
            utc_due_datetime = False
            utc_rec_datetime = False
            if due_datetime and due_datetime[-3] == ':':
                due_datetime = due_datetime[:-3] + due_datetime[-2:]
                due_datetime_obj = datetime.datetime.strptime(due_datetime, "%Y-%m-%dT%H:%M:%S%z")
                utc_due_datetime = due_datetime_obj.astimezone(timezone("UTC")).replace()

            rec_datetime = element.get("RecDateTime")
            if rec_datetime and rec_datetime[-3] == ':':
                rec_datetime = rec_datetime[:-3] + rec_datetime[-2:]
                rec_datetime_obj = datetime.datetime.strptime(rec_datetime, "%Y-%m-%dT%H:%M:%S%z")
                utc_rec_datetime = rec_datetime_obj.astimezone(timezone("UTC")).replace()
            self.env["seller.einvoice.line.wizard"].create({
                "invoice_amount": float(element.get("Amount", 0)),
                "buyer_tin": element.get("BuyerTin"),
                "inv_number": element.get("DocNumber"),
                "due_datetime": utc_due_datetime,
                "rec_datetime": utc_rec_datetime,
                "eic": element.get("EIC"),
                "party_type": element.get("PartyType"),
                "seller_tin": element.get("SellerTin"),
                "status": element.get("Status"),
                "einv_wizard_id": self.id,
                "output": element.get("Pdf")
            })

    def multiple_einvoice_change_status(self):
        if self.seller_einv_line_ids:
            selected_e_invoices = self.seller_einv_line_ids.filtered(lambda env_line: env_line.select)
            if not self.change_status_to:
                raise ValidationError("Select the status first!!!")
            if selected_e_invoices and len(selected_e_invoices) <= 100:
                company_id = self.env.user.company_id
                company_p12_certificate = company_id.p12_certificate
                company_p12_certificate = base64.b64decode(company_p12_certificate)
                certificate_password = company_id.certificate_password.encode('utf-8')
                final_xml = change_status.change_e_invoice_status(company_p12_certificate=company_p12_certificate,
                                                                  certificate_password=certificate_password,
                                                                  eics=selected_e_invoices.mapped("eic"),
                                                                  new_status=self.change_status_to)

                url = company_id.einvoice_endpoint
                try:
                    response = make_http_call(final_xml, url)
                except requests.exceptions.RequestException as e:  # This is the correct syntax
                    raise ValidationError(e)
                root = etree.fromstring(response)
                for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}ResponseCode'):
                    self.response = element.text

                for faultcode in root.iter('faultcode'):
                    for faultstring in root.iter('faultstring'):
                        raise ValidationError(
                            "Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))

            else:
                if len(selected_e_invoices) > 100:
                    raise ValidationError(
                        "Sorry can't update more than 100 invoices, Max limit: Only 100 invoices in one request!")
                else:
                    raise ValidationError(
                        "Sorry can't update! At least select one invoice.")


class SellerEInvoiceLineWizard(models.TransientModel):
    _name = "seller.einvoice.line.wizard"

    select = fields.Boolean()
    invoice_amount = fields.Float("Amount")
    buyer_tin = fields.Char("Buyer TIN")
    inv_number = fields.Char("Doc. Number")
    due_datetime = fields.Datetime("Due Datetime")
    eic = fields.Char("EIC")
    party_type = fields.Char()
    rec_datetime = fields.Datetime()
    seller_tin = fields.Char("Seller TIN")
    status = fields.Char()
    einv_wizard_id = fields.Many2one("seller.einvoice.wizard")
    output = fields.Binary(readonly=True)
    file_name = fields.Char()

    def accept_einvoice(self):
        self.change_einvoice_status(status="ACCEPTED")

    def refuse_einvoice(self):
        self.change_einvoice_status(status="REFUSED")

    def change_einvoice_status(self, status):
        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')
        final_xml = change_status.change_e_invoice_status(company_p12_certificate=company_p12_certificate,
                                                          certificate_password=certificate_password, eics=[self.eic],
                                                          new_status=status)

        url = company_id.einvoice_endpoint
        try:
            response = make_http_call(final_xml, url)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise ValidationError(e)
        root = etree.fromstring(response)
        for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}ResponseCode'):
            self.einv_wizard_id.response = element.text

        for faultcode in root.iter('faultcode'):
            for faultstring in root.iter('faultstring'):
                raise ValidationError("Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))

    def get_e_invoice_pdf(self):
        company_id = self.env.user.company_id
        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')
        if self.output:
            self.file_name = "E-Invoice " + self.inv_number + ".pdf"
            url = "web/binary/download_pdf_document?model=seller.einvoice.line.wizard&rec_id={}&filename={}".format(
                self.id,
                self.file_name)
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'download',
                'tag': 'reload',
            }

        elif self.eic:
            eic = self.eic
            final_xml = fetch_e_invoice.fetch_e_invoice(company_p12_certificate=company_p12_certificate,
                                                        certificate_password=certificate_password, eic=eic)
            url = company_id.einvoice_endpoint
            try:
                response = make_http_call(final_xml, url)
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                raise ValidationError(e)
            pdf = None
            root = etree.fromstring(response)
            for element in root.iter('{https://Einvoice.tatime.gov.al/EinvoiceService/schema}Pdf'):
                pdf = element.text
            if pdf:
                self.output = pdf
                self.file_name = "E-Invoice " + self.inv_number + ".pdf"
                url = "web/binary/download_pdf_document?model=seller.einvoice.line.wizard&rec_id={}&filename={}".format(
                    self.id,
                    self.file_name)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'download',
                    'tag': 'reload',
                }

