import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring

from .qr_codes.make_wtn_qr_code import make_wtn_qr_code

from .utils.digital_signature import sign_xml
from .utils.constants import envelope_start, envelope_end


def make_wtn(data):
    header_dictionary = {}
    wtn_dictionary = {}
    issuer_dictionary = {}
    carrier_dictionary = {}
    items_dictionary = {}

    xml_root = Element('RegisterWTNRequest',
                       {
                           'xmlns': 'https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema',
                           'Id': 'Request',
                           'Version': '3',
                       }, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#',
                                 })

    # Header
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

    header_subseq_deliv_type = data.get('SubseqDelivType')
    if (header_subseq_deliv_type):
        header_dictionary['SubseqDelivType'] = header_subseq_deliv_type

    # header_source = ''
    # header_dictionary['Source'] = header_source

    # WTN
    wtn_type = data.get('Type')
    if (wtn_type):
        wtn_dictionary['Type'] = wtn_type

    wtn_transaction = data.get('Transaction')
    if (wtn_transaction):
        wtn_dictionary['Transaction'] = wtn_transaction

    wtn_issue_date_time = data.get('IssueDateTime')
    if (wtn_issue_date_time):
        wtn_dictionary['IssueDateTime'] = wtn_issue_date_time

    wtn_operator_code = data.get('OperatorCode')
    if (wtn_operator_code):
        wtn_dictionary['OperatorCode'] = wtn_operator_code

    wtn_busin_unit_code = data.get('BusinUnitCode')
    if (wtn_busin_unit_code):
        wtn_dictionary['BusinUnitCode'] = wtn_busin_unit_code

    wtn_soft_code = data.get('SoftCode')
    if (wtn_soft_code):
        wtn_dictionary['SoftCode'] = wtn_soft_code

    wtn_wtn_ord_num = data.get('WTNOrdNum')
    if (wtn_wtn_ord_num):
        wtn_dictionary['WTNOrdNum'] = wtn_wtn_ord_num

    wtn_wtn_num = data.get('WTNNum')
    if (wtn_wtn_num):
        wtn_dictionary['WTNNum'] = wtn_wtn_num

    wtn_value_of_goods = data.get('ValueOfGoods')
    if (wtn_value_of_goods):
        wtn_dictionary['ValueOfGoods'] = wtn_value_of_goods

    wtn_veh_ownership = data.get('VehOwnership')
    if (wtn_veh_ownership):
        wtn_dictionary['VehOwnership'] = wtn_veh_ownership

    wtn_veh_plates = data.get('VehPlates')
    if (wtn_veh_plates):
        wtn_dictionary['VehPlates'] = wtn_veh_plates

    wtn_start_addr = data.get('StartAddr')
    if (wtn_start_addr):
        wtn_dictionary['StartAddr'] = wtn_start_addr

    wtn_start_city = data.get('StartCity')
    if (wtn_start_city):
        wtn_dictionary['StartCity'] = wtn_start_city

    wtn_start_date_time = data.get('StartDateTime')
    if (wtn_start_date_time):
        wtn_dictionary['StartDateTime'] = wtn_start_date_time

    wtn_start_point = data.get('StartPoint')
    if (wtn_start_point):
        wtn_dictionary['StartPoint'] = wtn_start_point

    wtn_destin_addr = data.get('DestinAddr')
    if (wtn_destin_addr):
        wtn_dictionary['DestinAddr'] = wtn_destin_addr

    wtn_destin_city = data.get('DestinCity')
    if (wtn_destin_city):
        wtn_dictionary['DestinCity'] = wtn_destin_city

    wtn_destin_date_time = data.get('DestinDateTime')
    if (wtn_destin_date_time):
        wtn_dictionary['DestinDateTime'] = wtn_destin_date_time

    wtn_destin_point = data.get('DestinPoint')
    if (wtn_destin_point):
        wtn_dictionary['DestinPoint'] = wtn_destin_point

    wtn_is_goods_flammable = data.get('IsGoodsFlammable')
    if (wtn_is_goods_flammable):
        wtn_dictionary['IsGoodsFlammable'] = wtn_is_goods_flammable

    wtn_is_escort_required = data.get('IsEscortRequired')
    if (wtn_is_escort_required):
        wtn_dictionary['IsEscortRequired'] = wtn_is_escort_required

    wtn_pack_type = data.get('PackType')
    if (wtn_pack_type):
        wtn_dictionary['PackType'] = wtn_pack_type

    wtn_pack_num = data.get('PackNum')
    if (wtn_pack_num):
        wtn_dictionary['PackNum'] = wtn_pack_num

    wtn_items_num = data.get('ItemsNum')
    if (wtn_items_num):
        wtn_dictionary['ItemsNum'] = wtn_items_num

    wtn_wtnic = data.get('WTNIC')
    if (wtn_wtnic):
        wtn_dictionary['WTNIC'] = wtn_wtnic

    wtn_wtnic_signature = data.get('WTNICSignature')
    if (wtn_wtnic_signature):
        wtn_dictionary['WTNICSignature'] = wtn_wtnic_signature

    # WTN->Issuer
    wtn_issuer_nuis = data.get('Issuer-NUIS')
    if (wtn_issuer_nuis):
        issuer_dictionary['NUIS'] = wtn_issuer_nuis

    wtn_issuer_name = data.get('Issuer-Name')
    if (wtn_issuer_name):
        issuer_dictionary['Name'] = wtn_issuer_name

    wtn_issuer_address = data.get('Issuer-Address')
    if (wtn_issuer_address):
        issuer_dictionary['Address'] = wtn_issuer_address

    wtn_issuer_town = data.get('Issuer-Town')
    if (wtn_issuer_town):
        issuer_dictionary['Town'] = wtn_issuer_town

    # WTN->Carrier
    wtn_carrier_id_type = data.get('Carrier-IDType')
    if (wtn_carrier_id_type):
        carrier_dictionary['IDType'] = wtn_carrier_id_type

    wtn_carrier_id_num = data.get('Carrier-IDNum')
    if (wtn_carrier_id_num):
        carrier_dictionary['IDNum'] = wtn_carrier_id_num

    wtn_carrier_name = data.get('Carrier-Name')
    if (wtn_carrier_name):
        carrier_dictionary['Name'] = wtn_carrier_name

    wtn_carrier_address = data.get('Carrier-Address')
    if (wtn_carrier_address):
        carrier_dictionary['Address'] = wtn_carrier_address

    wtn_carrier_town = data.get('Carrier-Town')
    if (wtn_carrier_town):
        carrier_dictionary['Town'] = wtn_carrier_town

    # WTN->Items
    # WTN->Items->I
    wtn_i_n = data.get('I-N')
    if (wtn_i_n):
        items_dictionary['N'] = wtn_i_n

    wtn_i_c = data.get('I-C')
    if (wtn_i_c):
        items_dictionary['C'] = wtn_i_c

    wtn_i_u = data.get('I-U')
    if (wtn_i_u):
        items_dictionary['U'] = wtn_i_u

    wtn_i_q = data.get('I-Q')
    if (wtn_i_q):
        items_dictionary['Q'] = wtn_i_q

    SubElement(xml_root, 'Header', header_dictionary)
    wtn_subelement = SubElement(xml_root, 'WTN', wtn_dictionary)
    SubElement(wtn_subelement, 'Issuer', issuer_dictionary)
    SubElement(wtn_subelement, 'Carrier', carrier_dictionary)
    items_subelement = SubElement(wtn_subelement, 'Items')
    SubElement(items_subelement, 'I', items_dictionary)

    signed_root = tostring(sign_xml(xml_root))
    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end

    make_wtn_qr_code(
        wtn_wtnic, wtn_issuer_nuis, wtn_issue_date_time, wtn_wtn_ord_num,
        wtn_busin_unit_code, wtn_soft_code
    )

    return final_xml
