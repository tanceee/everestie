import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring
from odoo.addons.fiscalization_base.services.utils.constants import envelope_start, envelope_end
from odoo.addons.fiscalization_base.services.utils.digital_signature import sign_xml


def make_wtn(data, company_p12_certificate, certificate_password):
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
                       }, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#'})

    # Header
    header_uuid = data.get('UUID')
    if not header_uuid:
        header_uuid = str(uuid.uuid4())
    if header_uuid:
        header_dictionary['UUID'] = header_uuid

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')

    header_send_date_time = data.get('issue_date_time')
    if not header_send_date_time:
        header_send_date_time = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
    if header_send_date_time:
        issue_date_time = header_send_date_time.replace(
            tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
            microsecond=0).isoformat()
        header_dictionary['SendDateTime'] = issue_date_time

    header_subseq_deliv_type = data.get('subsequent_delivery_type')
    if header_subseq_deliv_type:
        header_dictionary['SubseqDelivType'] = header_subseq_deliv_type

    # header_source = ''
    # header_dictionary['Source'] = header_source

    # WTN
    wtn_type = data.get('wtn_type')
    if wtn_type:
        wtn_dictionary['Type'] = wtn_type

    wtn_transaction = data.get('wtn_transaction')
    if wtn_transaction:
        wtn_dictionary['Transaction'] = wtn_transaction

    wtn_issue_date_time = data.get('issue_date_time')
    if wtn_issue_date_time:
        wtn_dictionary['IssueDateTime'] = wtn_issue_date_time.replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
    else:
        wtn_dictionary['IssueDateTime'] = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()

    wtn_operator_code = data.get('operator_code')
    if wtn_operator_code:
        wtn_dictionary['OperatorCode'] = wtn_operator_code

    wtn_busin_unit_code = data.get('busin_unit_code')
    if wtn_busin_unit_code:
        wtn_dictionary['BusinUnitCode'] = wtn_busin_unit_code

    wtn_soft_code = data.get('soft_code')
    if wtn_soft_code:
        wtn_dictionary['SoftCode'] = wtn_soft_code

    wtn_wtn_ord_num = data.get('wtn_ordinal_number')
    if wtn_wtn_ord_num:
        wtn_dictionary['WTNOrdNum'] = wtn_wtn_ord_num

    wtn_wtn_num = data.get('wth_number')
    if wtn_wtn_num:
        wtn_dictionary['WTNNum'] = wtn_wtn_num

    wtn_value_of_goods = data.get('value_of_goods')
    if wtn_value_of_goods:
        wtn_dictionary['ValueOfGoods'] = str("{:.2f}".format(wtn_value_of_goods))

    wtn_veh_ownership = data.get('veh_ownership')
    if wtn_veh_ownership:
        wtn_dictionary['VehOwnership'] = wtn_veh_ownership

    wtn_veh_plates = data.get('veh_plates')
    if wtn_veh_plates:
        wtn_dictionary['VehPlates'] = wtn_veh_plates

    wtn_start_addr = data.get('start_address')
    if wtn_start_addr:
        wtn_dictionary['StartAddr'] = wtn_start_addr

    wtn_start_city = data.get('start_city')
    if wtn_start_city:
        wtn_dictionary['StartCity'] = wtn_start_city

    wtn_start_date_time = data.get('start_date_time')
    if wtn_start_date_time:
        wtn_dictionary['StartDateTime'] = wtn_start_date_time.replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()

    wtn_start_point = data.get('start_point')
    if wtn_start_point:
        wtn_dictionary['StartPoint'] = wtn_start_point

    wtn_destin_addr = data.get('des_address')
    if wtn_destin_addr:
        wtn_dictionary['DestinAddr'] = wtn_destin_addr

    wtn_destin_city = data.get('des_city')
    if wtn_destin_city:
        wtn_dictionary['DestinCity'] = wtn_destin_city

    wtn_destin_date_time = data.get('des_date_time')
    if wtn_destin_date_time:
        wtn_dictionary['DestinDateTime'] = wtn_destin_date_time.replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()

    wtn_destin_point = data.get('des_point')
    if wtn_destin_point:
        wtn_dictionary['DestinPoint'] = wtn_destin_point

    wtn_is_goods_flammable = data.get('is_goods_flammable')
    if wtn_is_goods_flammable:
        wtn_dictionary['IsGoodsFlammable'] = 'true'
    else:
        wtn_dictionary['IsGoodsFlammable'] = 'false'

    wtn_is_escort_required = data.get('is_escort_required')
    if wtn_is_escort_required:
        wtn_dictionary['IsEscortRequired'] = 'true'
    else:
        wtn_dictionary['IsEscortRequired'] = 'false'

    wtn_pack_type = data.get('pack_type')
    if wtn_pack_type:
        wtn_dictionary['PackType'] = wtn_pack_type

    wtn_pack_num = data.get('pack_num')
    if wtn_pack_num:
        wtn_dictionary['PackNum'] = str(wtn_pack_num)

    wtn_items_num = data.get('items_num')
    if wtn_items_num:
        wtn_dictionary['ItemsNum'] = str(wtn_items_num)

    wtn_wtnic = data.get('wtnic')
    if wtn_wtnic:
        wtn_dictionary['WTNIC'] = wtn_wtnic

    wtn_wtnic_signature = data.get('wtnic_signature')
    if wtn_wtnic_signature:
        wtn_dictionary['WTNICSignature'] = wtn_wtnic_signature

    # WTN->Issuer
    wtn_issuer_nuis = data.get('issuer_nuis')
    if wtn_issuer_nuis:
        issuer_dictionary['NUIS'] = wtn_issuer_nuis

    wtn_issuer_name = data.get('issuer_name')
    if wtn_issuer_name:
        issuer_dictionary['Name'] = wtn_issuer_name

    wtn_issuer_address = data.get('issuer_address')
    if wtn_issuer_address:
        issuer_dictionary['Address'] = wtn_issuer_address

    wtn_issuer_town = data.get('issuer_town')
    if wtn_issuer_town:
        issuer_dictionary['Town'] = wtn_issuer_town

    # WTN->Carrier
    wtn_carrier_id_type = data.get('carrier_id_type')
    if wtn_carrier_id_type:
        carrier_dictionary['IDType'] = wtn_carrier_id_type

    wtn_carrier_id_num = data.get('carrier_id_num')
    if wtn_carrier_id_num:
        carrier_dictionary['IDNum'] = wtn_carrier_id_num

    wtn_carrier_name = data.get('carrier_name')
    if wtn_carrier_name:
        carrier_dictionary['Name'] = wtn_carrier_name

    wtn_carrier_address = data.get('carrier_address')
    if wtn_carrier_address:
        carrier_dictionary['Address'] = wtn_carrier_address

    wtn_carrier_town = data.get('carrier_town')
    if wtn_carrier_town:
        carrier_dictionary['Town'] = wtn_carrier_town

    # WTN->Items
    # WTN->Items->I
    list_items_dictionaries = []
    items = data['move_ids_without_package']
    # print("items ?????????", items)
    for item in items:
        item_dictionary = {}
        product_id = getattr(item, 'product_id')
        # print("PR", product_id.name)
        item_name = product_id.name
        if item_name:
            item_dictionary['N'] = item_name

        # product_id = (getattr(i, 'product_id'))
        item_code = product_id.default_code
        if item_code:
            item_dictionary['C'] = item_code

        product_uom = getattr(item, 'product_uom')
        product_uom_name = product_uom.name
        if product_uom_name:
            item_dictionary['U'] = product_uom_name

        item_done_qty = str("{:.2f}".format(getattr(item, 'quantity_done')))
        if item_done_qty:
            item_dictionary['Q'] = item_done_qty
        list_items_dictionaries.append(item_dictionary)

    SubElement(xml_root, 'Header', header_dictionary)
    print(">>>>>>", wtn_dictionary)
    wtn_subelement = SubElement(xml_root, 'WTN', wtn_dictionary)
    SubElement(wtn_subelement, 'Issuer', issuer_dictionary)
    if carrier_dictionary:
        SubElement(wtn_subelement, 'Carrier', carrier_dictionary)
    items_subelement = SubElement(wtn_subelement, 'Items')
    # print("list_items_dictionaries", list_items_dictionaries)
    for i_dictionary in list_items_dictionaries:
        SubElement(items_subelement, 'I', i_dictionary)

    signed_root = tostring(sign_xml(xml_root, company_p12_certificate=company_p12_certificate,
                                    certificate_password=certificate_password))
    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end

    return final_xml
