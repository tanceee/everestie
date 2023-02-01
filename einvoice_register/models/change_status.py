import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring
from odoo.addons.fiscalization_base.services.utils.constants import envelope_start, envelope_end
from odoo.addons.fiscalization_base.services.utils.digital_signature import sign_xml


def change_e_invoice_status(company_p12_certificate, certificate_password, eics, new_status):
    header_dictionary = {}
    xml_root = Element('EinvoiceChangeStatusRequest',
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

    SubElement(xml_root, 'Header', header_dictionary)
    if eics:
        eics_sub_element = SubElement(xml_root, 'EICs')
        for eic in eics:
            eic_sub_element = SubElement(eics_sub_element, 'EIC')
            eic_sub_element.text = eic

        ein_status_sub_element = SubElement(xml_root, 'EinStatus')
        ein_status_sub_element.text = new_status

    signed_root = tostring(
        sign_xml(xml_root, company_p12_certificate=company_p12_certificate, certificate_password=certificate_password))

    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end
    print("FINAL XML", final_xml)

    return final_xml
