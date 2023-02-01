import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring
from .utils.digital_signature import sign_xml
from .utils.constants import envelope_start, envelope_end

def make_tcr(data,company_p12_certificate,certificate_password):
    header_dictionary = {}
    tcr_dictionary = {}

    xml_root = Element('RegisterTCRRequest',
                       {
                           'xmlns': 'https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema',
                           'Id': 'Request',
                           'Version': '3',
                       }, nsmap={
            'ns2': 'http://www.w3.org/2000/09/xmldsig#', })

    header_uuid = data.get('UUID')
    if (not header_uuid):
        header_uuid = str(uuid.uuid4())
    if (header_uuid):
        header_dictionary['UUID'] = header_uuid

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')
    header_send_date_time = data.get('SendDateTime')
    if (not header_send_date_time):
        header_send_date_time = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
    if (header_send_date_time):
        header_dictionary['SendDateTime'] = header_send_date_time


    tcr_issuer_nuis = data.get('IssuerNUIS')
    if (tcr_issuer_nuis):
        tcr_dictionary['IssuerNUIS'] = tcr_issuer_nuis

    tcr_busin_unit_code = data.get('BusinUnitCode')
    if (tcr_busin_unit_code):
        tcr_dictionary['BusinUnitCode'] = tcr_busin_unit_code

    tcr_int_id = data.get('TCRIntID')
    if (tcr_int_id):
        tcr_dictionary['TCRIntID'] = tcr_int_id

    tcr_soft_code = data.get('SoftCode')
    if (tcr_soft_code):
        tcr_dictionary['SoftCode'] = tcr_soft_code

    tcr_maintainer_code = data.get('MaintainerCode')
    if (tcr_maintainer_code):
        tcr_dictionary['MaintainerCode'] = tcr_maintainer_code

    tcr_valid_from = data.get('ValidFrom')
    if (tcr_valid_from):
        tcr_dictionary['ValidFrom'] = tcr_valid_from

    tcr_valid_to = data.get('ValidTo')
    if (tcr_valid_to):
        tcr_dictionary['ValidTo'] = tcr_valid_to

    tcr_type = data.get('Type')
    if (tcr_type):
        tcr_dictionary['Type'] = tcr_type

    SubElement(xml_root, 'Header', header_dictionary)
    SubElement(xml_root, 'TCR', tcr_dictionary)

    signed_root = tostring(sign_xml(xml_root,company_p12_certificate=company_p12_certificate,
                                  certificate_password=certificate_password))

    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end

    return final_xml
