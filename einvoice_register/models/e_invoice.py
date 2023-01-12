# -*- coding: utf-8 -*-
import base64
import datetime
import uuid

from dateutil import tz
from lxml import etree
from lxml.etree import Element, SubElement, tostring
from odoo.addons.fiscalization_base.services.utils.constants import envelope_start, envelope_end
from odoo.addons.fiscalization_base.services.utils.digital_signature import sign_xml


# from ..services.utils.constants import envelope_end
# from ..services.utils.constants import envelope_start
# from ..services.utils.digital_signature import sign_xml


# TEST_URL = "https://einvoice-test.tatime.gov.al/EinvoiceService-v1/EinvoiceService.wsdl"
# HEADERS = {'content-type': 'text/xml'}


# temp_dict = {'issuer_nuis': 'L62316009V', "busin_unit_code": "ll996sf167", "tcr_code": "vc813ms173",
#              "soft_code": "bi558ej110", "operator_code": "pb999gp965"}


def make_e_invoice(xml_ubl_invoice_content, ubl_wrapper_tag, company_p12_certificate, certificate_password):
    header_dictionary = {}
    xml_root = Element('RegisterEinvoiceRequest',
                       {'xmlns': 'https://Einvoice.tatime.gov.al/EinvoiceService/schema', 'Id': 'Request',
                        'Version': '1', }, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#'})

    # Header
    # header_uuid = data.get('UUID')
    header_uuid = str(uuid.uuid4())
    if header_uuid:
        header_dictionary['UUID'] = header_uuid

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')
    # header_send_date_time = data.get('header_send_datetime')
    # if (not header_send_date_time):
    header_send_date_time = datetime.datetime.utcnow().replace(
        tzinfo=from_zone).astimezone(to_zone).replace(
        microsecond=0).isoformat()
    if header_send_date_time:
        header_dictionary['SendDateTime'] = header_send_date_time

    # header_subseq_deliv_type = data.get('SubseqDelivType')
    # if (header_subseq_deliv_type):
    #     header_dictionary['SubseqDelivType'] = header_subseq_deliv_type

    # EinvoiceEnvelope

    SubElement(xml_root, 'Header', header_dictionary)

    e_invoice_envelope_sub_element = SubElement(xml_root, 'EinvoiceEnvelope')
    ubl_invoice_sub_element = SubElement(e_invoice_envelope_sub_element, ubl_wrapper_tag)

    xml_etree = etree.fromstring(xml_ubl_invoice_content)
    signed_invoice = tostring(
        sign_xml(xml_etree, company_p12_certificate=company_p12_certificate, certificate_password=certificate_password))

    signed_ubl_invoice_b64 = base64.b64encode(signed_invoice)
    ubl_invoice_sub_element.text = signed_ubl_invoice_b64
    signed_root = tostring(
        sign_xml(xml_root, company_p12_certificate=company_p12_certificate, certificate_password=certificate_password))

    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end
    print("FINAL XML", final_xml)
    return final_xml
