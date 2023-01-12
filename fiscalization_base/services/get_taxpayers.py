import datetime
import uuid

from lxml.etree import Element, SubElement, tostring

from dateutil import tz
from odoo.addons.fiscalization_base.services.utils.constants import envelope_start, envelope_end
from odoo.addons.fiscalization_base.services.utils.digital_signature import sign_xml


def get_taxpayers_req_data(input_data, company_p12_certificate, certificate_password):
    header_dictionary = {}
    xml_root = Element('GetTaxpayersRequest',
                       {
                           'xmlns': 'https://Einvoice.tatime.gov.al/EinvoiceService/schema',
                           'Id': 'Request',
                           'Version': '1',
                       }, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#'})

    # Header
    header_uuid = str(uuid.uuid4())
    if header_uuid:
        header_dictionary['UUID'] = header_uuid

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')

    header_send_date_time = datetime.datetime.utcnow().replace(
        tzinfo=from_zone).astimezone(to_zone).replace(
        microsecond=0).isoformat()
    if header_send_date_time:
        header_dictionary['SendDateTime'] = header_send_date_time

    SubElement(xml_root, 'Header', header_dictionary)
    filter_element = SubElement(xml_root, 'Filter')

    taxpayer_vat = SubElement(filter_element, 'Tin')
    taxpayer_vat.text = input_data
    signed_root = tostring(sign_xml(xml_root, company_p12_certificate=company_p12_certificate,
                                    certificate_password=certificate_password))
    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end
    return final_xml
