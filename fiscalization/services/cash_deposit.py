import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring
from .utils.digital_signature import sign_xml
from .utils.constants import envelope_start, envelope_end

def make_cash_deposit(data,company_p12_certificate, certificate_password):
    header_dictionary = {}
    cash_deposit_dictionary = {}

    xml_root = Element('RegisterCashDepositRequest',
                       {
                           'xmlns': 'https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema',
                           'Id': 'Request',
                           'Version': '3',
                       }, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#',
                                 })

    header_dictionary['UUID'] = str(uuid.uuid4())

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')
    header_send_date_time = data.get('SendDateTime')
    if (not header_send_date_time):
        header_send_date_time = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
    if (header_send_date_time):
        header_dictionary['SendDateTime'] = header_send_date_time

    header_subseq_deliv_type = data.get('SubseqDelivType')
    if (header_subseq_deliv_type):
        header_dictionary['SubseqDelivType'] = header_subseq_deliv_type



    # cash_deposit_change_date_time = data.get('change_date_time')
    # if (cash_deposit_change_date_time):
    cash_deposit_dictionary[
        'ChangeDateTime'] = datetime.datetime.utcnow().replace(
        tzinfo=from_zone).astimezone(to_zone).replace(
        microsecond=0).isoformat()

    cash_deposit_operation = data.get('operation')
    if (cash_deposit_operation):
        cash_deposit_dictionary['Operation'] = cash_deposit_operation

    cash_deposit_cash_amt = data.get('cash_amt')
    if (cash_deposit_cash_amt):
        cash_deposit_dictionary['CashAmt'] = cash_deposit_cash_amt

    cash_deposit_tcr_code = data.get('tcr_code')
    if (cash_deposit_tcr_code):
        cash_deposit_dictionary['TCRCode'] = cash_deposit_tcr_code

    cash_deposit_issuer_nuis = data.get('issuer_nuis')
    if (cash_deposit_issuer_nuis):
        cash_deposit_dictionary['IssuerNUIS'] = cash_deposit_issuer_nuis

    SubElement(xml_root, 'Header', header_dictionary)
    SubElement(xml_root, 'CashDeposit', cash_deposit_dictionary)

    signed_root = tostring(sign_xml(xml_root,company_p12_certificate=company_p12_certificate,
                                  certificate_password=certificate_password))
    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end

    return final_xml
