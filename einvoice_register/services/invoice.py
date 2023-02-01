import datetime
import uuid

from dateutil import tz
from lxml.etree import Element, SubElement, tostring
from odoo.addons.fiscalization_base.services.utils.constants import envelope_start, envelope_end
from odoo.addons.fiscalization_base.services.utils.digital_signature import sign_xml


# from .utils.constants import envelope_start, envelope_end
# from .utils.digital_signature import sign_xml


def make_invoice(data, company_p12_certificate, certificate_password):
    header_dictionary = {}
    invoice_dictionary = {}
    correctiveinv_dictionary = {}
    baddebtinv_dictionary = {}
    # suminviicref_dictionary = {}
    supplydateorperiod_dictionary = {}
    paymethod_dictionary = {}
    # voucher_dictionary = {}
    currency_dictionary = {}
    seller_dictionary = {}
    buyer_dictionary = {}
    # i_dictionary = {}
    # vd_dictionary = {}
    # v_dictionary = {}
    # sametax_dictionary = {}
    # constax_dictionary = {}
    # fee_dictionary = {}
    coff = 1
    if data['move_type'] == 'out_refund':
        coff = -1
    xml_root = Element('RegisterInvoiceRequest',
                       {'xmlns': 'https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema', 'Id': 'Request',
                        'Version': '3'}, nsmap={'ns2': 'http://www.w3.org/2000/09/xmldsig#'})

    # Header
    header_uuid = data.get('UUID')
    if not header_uuid:
        header_uuid = str(uuid.uuid4())
    if header_uuid:
        header_dictionary['UUID'] = header_uuid

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Tirane')

    header_send_date_time = data.get('header_send_datetime')
    if not header_send_date_time:
        header_send_date_time = datetime.datetime.utcnow().replace(tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
    if header_send_date_time:
        header_dictionary['SendDateTime'] = header_send_date_time

    header_subseq_deliv_type = data.get('SubseqDelivType')
    if header_subseq_deliv_type:
        header_dictionary['SubseqDelivType'] = header_subseq_deliv_type

    # header_source = ''
    # header_dictionary['Source'] = header_source

    # Invoice
    invoice_type_of_inv = data.get('type_of_invoice')
    print("%%%%%%%%%%%%%", invoice_type_of_inv)
    if invoice_type_of_inv:
        invoice_dictionary['TypeOfInv'] = invoice_type_of_inv

    invoice_type_of_self_iss = data.get('type_of_self_iss')
    if invoice_type_of_self_iss:
        invoice_dictionary['TypeOfSelfIss'] = invoice_type_of_self_iss

    invoice_is_simplified_inv = data.get('is_simplified_invoice')
    if invoice_is_simplified_inv:
        invoice_dictionary['IsSimplifiedInv'] = invoice_is_simplified_inv

    # invoice_issue_date_time = data.get('invoice_datetime')
    invoice_issue_date_time = data.get('header_send_datetime')  # TODO Check datetime
    if not invoice_issue_date_time:
        invoice_issue_date_time = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
            microsecond=0).isoformat()
    if invoice_issue_date_time:
        invoice_dictionary['IssueDateTime'] = invoice_issue_date_time

    invoice_inv_num = data.get('invoice_number')
    if invoice_inv_num:
        invoice_dictionary['InvNum'] = invoice_inv_num

    invoice_inv_ord_num = data.get('invoice_order_number')
    if invoice_inv_ord_num:
        invoice_dictionary['InvOrdNum'] = invoice_inv_ord_num

    # invoice_tcr_code = data.get('tcr_code')
    # if (invoice_tcr_code):
    #     invoice_dictionary['TCRCode'] = invoice_tcr_code

    invoice_is_issuer_in_vat = data.get('company_id_is_in_vat')
    if invoice_is_issuer_in_vat:
        invoice_dictionary['IsIssuerInVAT'] = 'true'
    else:
        invoice_dictionary['IsIssuerInVAT'] = 'false'

    invoice_tax_free_amt = data.get('invoice_tax_free_amount')
    if invoice_tax_free_amt:
        invoice_dictionary['TaxFreeAmt'] = invoice_tax_free_amt

    invoice_mark_up_amt = data.get('invoice_markup_amount')
    if invoice_mark_up_amt:
        invoice_dictionary['MarkUpAmt'] = invoice_mark_up_amt

    invoice_goods_ex_amt = data.get('invoice_goods_exported_amount')
    if invoice_goods_ex_amt:
        invoice_dictionary['GoodsExAmt'] = invoice_goods_ex_amt

    invoice_tot_price_wo_vat = data.get('invoice_total_amount_without_vat')
    if invoice_tot_price_wo_vat:
        invoice_dictionary['TotPriceWoVAT'] = invoice_tot_price_wo_vat

    invoice_tot_vat_amt = data.get('vat_amt')
    if invoice_tot_vat_amt:
        invoice_dictionary['TotVATAmt'] = invoice_tot_vat_amt

    invoice_tot_price = data.get('amount_total')
    # if invoice_tot_price:
    invoice_dictionary['TotPrice'] = str(
        "{:.2f}".format(float(invoice_tot_price) * coff * data.get('currency_rate')))
    # invoice_tot_price = str("{:.2f}".format(float(invoice_tot_price)))

    invoice_operator_code = data.get('operator_code')
    if invoice_operator_code:
        invoice_dictionary['OperatorCode'] = invoice_operator_code

    invoice_busin_unit_code = data.get('busin_unit_code')
    if invoice_busin_unit_code:
        invoice_dictionary['BusinUnitCode'] = invoice_busin_unit_code

    invoice_soft_code = data.get('soft_code')
    if invoice_soft_code:
        invoice_dictionary['SoftCode'] = invoice_soft_code

    # invoice_imp_cust_dec_num = data.get('invoice_import_custom_declare_number')
    # if (invoice_imp_cust_dec_num):
    #     invoice_dictionary['ImpCustDecNum'] = invoice_imp_cust_dec_num

    # iic_input = iic.build_iic_input(issuer_nipt=invoice_issuer_nuis,
    #                                 datetime_created=invoice_issue_date_time,
    #                                 invoice_number=invoice_inv_num,
    #                                 business_unit_code=invoice_busin_unit_code,
    #                                 tcr_code=invoice_tcr_code,
    #                                 soft_code=invoice_soft_code,
    #                                 total_price=invoice_tot_price)
    #
    # invoice_iic = iic.generate_iic(iic_input=iic_input)
    # invoice_iic_signature = iic.generate_iic_signature(iic_input=iic_input)

    invoice_dictionary['IIC'] = data.get("invoice_iic")

    invoice_dictionary['IICSignature'] = data.get('invoice_iic_signature')

    invoice_is_reverse_charge = data.get('is_reverse_charge')
    if invoice_is_reverse_charge:
        invoice_dictionary['IsReverseCharge'] = 'true'
    else:
        invoice_dictionary['IsReverseCharge'] = 'false'

    invoice_pay_deadline = data.get('due_date')
    if invoice_pay_deadline:
        # invoice_pay_deadline = datetime.datetime.combine(invoice_pay_deadline, datetime.time.min)
        invoice_dictionary['PayDeadline'] = invoice_pay_deadline.isoformat()
        # invoice_dictionary['PayDeadline'] = pytz.utc.localize(invoice_pay_deadline).astimezone(to_zone).replace(
        #     microsecond=0).isoformat()

    # invoice_is_einvoice = data.get('IsEinvoice')
    invoice_is_einvoice = "false" if data['is_export'] or data['is_reverse_charge'] or data['partner_id'].vat_type in [
        'ID', 'PASS',
        'SOC'] else "true"
    if invoice_is_einvoice:
        invoice_dictionary['IsEinvoice'] = invoice_is_einvoice

    # Invoice->CorrectiveInv
    # correctiveinv_iic_ref = data.get('CorrectiveInv-IICRef')
    reversed_entry_id = data.get('reversed_entry_id')
    is_bad_debt_invoice = data.get('is_bad_debt_invoice')

    if reversed_entry_id and not is_bad_debt_invoice:
        correctiveinv_iic_ref = reversed_entry_id.iic_code
        correctiveinv_dictionary['IICRef'] = correctiveinv_iic_ref

        correctiveinv_issue_date_time = reversed_entry_id.header_send_datetime
        if correctiveinv_issue_date_time:
            correctiveinv_dictionary['IssueDateTime'] = correctiveinv_issue_date_time

        # correctiveinv_type = data.get('CorrectiveInv-Type')
        # if (correctiveinv_type):
        correctiveinv_dictionary['Type'] = "CREDIT"

    # Invoice->BadDebtInv
    # baddebtinv_iic_ref = data.get('BadDebtInv-IICRef')
    if is_bad_debt_invoice:
        bad_debt_iic_ref = reversed_entry_id.iic_code
        baddebtinv_dictionary['IICRef'] = bad_debt_iic_ref
        bad_debt_issue_date_time = reversed_entry_id.header_send_datetime
        if bad_debt_issue_date_time:
            baddebtinv_dictionary['IssueDateTime'] = bad_debt_issue_date_time
    #     if
    #     baddebtinv_dictionary['IICRef'] = baddebtinv_iic_ref
    #
    # baddebtinv_issue_date_time = data.get('BadDebtInv-IssueDateTime')
    # if (baddebtinv_issue_date_time):
    #     baddebtinv_dictionary['IssueDateTime'] = baddebtinv_issue_date_time

    # Invoice->SumInvIICRefs
    # Invoice->SumInvIICRefs->SumInvIICRef
    # suminviicref_iic = data.get('SumInvIICRef-IIC')
    # if (suminviicref_iic):
    #     suminviicref_dictionary['IIC'] = suminviicref_iic
    #
    # suminviicref__issue_date_time = data.get(
    #     'SumInvIICRef-IssueDateTime')
    # if (suminviicref__issue_date_time):
    #     suminviicref_dictionary[
    #         'IssueDateTime'] = suminviicref__issue_date_time

    # Invoice->SupplyDateOrPeriod
    supplydateorperiod_start = data.get('start_date')
    if (supplydateorperiod_start):
        supplydateorperiod_dictionary['Start'] = supplydateorperiod_start.strftime('%Y-%m-%d')

    supplydateorperiod_end = data.get('end_date')
    if (supplydateorperiod_end):
        supplydateorperiod_dictionary['End'] = supplydateorperiod_end.strftime('%Y-%m-%d')

    # Invoice->Paymethods
    # Invoice->Paymethods->Paymethod
    paymethod_type = data.get('pay_method_type')
    if paymethod_type:
        paymethod_dictionary['Type'] = paymethod_type

    paymethod_amt = data.get('pay_method_amount')
    if paymethod_amt:
        paymethod_dictionary['Amt'] = paymethod_amt

    paymethod_comp_card = data.get('PayMethod-CompCard')
    if paymethod_comp_card:
        paymethod_dictionary['CompCard'] = paymethod_comp_card

        # Invoice->Paymethods->Paymethod->Vouchers
        # Invoice->Paymethods->Paymethod->Vouchers->Voucher
        # voucher_num = data.get('Voucher-Num')
        # if (voucher_num):
        #     voucher_dictionary['Num'] = voucher_num

        # momental
    # Invoice->Currency
    currency_code = data.get('invoice_currency_code')
    if currency_code != "ALL":
        if currency_code:
            currency_dictionary['Code'] = currency_code

        currency_ex_rate = data.get('exrate')
        if currency_ex_rate:
            currency_ex_rate = str("{:.2f}".format(currency_ex_rate))
            currency_dictionary['ExRate'] = currency_ex_rate

        # currency_is_buying = data.get('invoice_currency_is_buying')
        # if currency_is_buying == 'true':
        #     currency_dictionary['IsBuying'] = currency_is_buying

    # Invoice->Seller
    seller_id_type = data.get('invoice_seller_id_type')
    if seller_id_type:
        seller_dictionary['IDType'] = seller_id_type

    seller_id_num = data.get('invoice_seller_id_number')
    if seller_id_num:
        seller_dictionary['IDNum'] = seller_id_num

    seller_name = data.get('invoice_seller_id_name')
    if seller_name:
        seller_dictionary['Name'] = seller_name

    seller_address = data.get('invoice_seller_id_address')
    if seller_address:
        seller_dictionary['Address'] = seller_address

    seller_town = data.get('invoice_seller_id_city')
    if seller_town:
        seller_dictionary['Town'] = seller_town

    seller_country = data.get('invoice_seller_id_country')
    if seller_country:
        seller_dictionary['Country'] = seller_country

    # Invoice->Buyer
    buyer_id_type = data.get('invoice_buyer_id_type')
    if buyer_id_type:
        buyer_dictionary['IDType'] = buyer_id_type

    buyer_id_num = data.get('invoice_buyer_id_number')
    if buyer_id_num:
        buyer_dictionary['IDNum'] = buyer_id_num

    buyer_name = data.get('invoice_buyer_id_name')
    if buyer_name:
        buyer_dictionary['Name'] = buyer_name

    buyer_address = data.get('invoice_buyer_id_address')
    if buyer_address:
        buyer_dictionary['Address'] = buyer_address

    buyer_town = data.get('invoice_buyer_id_city')
    if buyer_town:
        buyer_dictionary['Town'] = buyer_town

    buyer_country = data.get('invoice_buyer_id_country')
    if buyer_country:
        buyer_dictionary['Country'] = buyer_country

    # Invoice->Items
    # Invoice->Items->I
    list_i_dictionaries = []

    for i in data['invoice_line_ids']:
        i_dictionary = {}
        vd_dictionary = {}
        v_dictionary = {}
        display_type = getattr(i, 'display_type')
        if display_type:
            continue
        i_n = getattr(i, 'name')
        if i_n:
            i_dictionary['N'] = i_n[:50]

        product_id = (getattr(i, 'product_id'))
        i_c = product_id.default_code
        if i_c:
            i_dictionary['C'] = i_c

        i_u = str(getattr(i, 'invoice_item_unit_of_measure'))
        if i_u:
            i_dictionary['U'] = i_u

        i_q = str("{:.2f}".format(getattr(i, 'quantity') * coff))
        if i_q:
            i_dictionary['Q'] = i_q

        tax_ids = getattr(i, 'tax_ids')
        price_unit = getattr(i, 'price_unit')
        currency = getattr(i, 'currency_id')
        currency_rate = getattr(i, 'move_id').currency_rate

        # qty = getattr(i, 'quantity')
        print("TAX IDS", tax_ids)
        tax_calc = tax_ids.compute_all(price_unit, currency, 1, product=None, partner=None)
        total_excluded = tax_calc['total_excluded']
        total_included = tax_calc['total_included']
        i_upb = str("{:.2f}".format(total_excluded * currency_rate))  # data['company_id']['vat_rate']
        if i_upb:
            i_dictionary['UPB'] = i_upb  # Unit price before Value added tax is applied

        # print("TAX>>>>>>>>>>>>>>>>")
        # tax_amount = 0
        # for tax in tax_calc['taxes']:
        #     tax_amount += tax['amount']
        # print("TAX cal", tax_calc)

        i_upa = str("{:.2f}".format(total_included * currency_rate))  # TODO Check UPA (Unit Price with VAT)

        if i_upa:
            i_dictionary['UPA'] = i_upa

        i_r = getattr(i, 'discount', None)
        if i_r:
            i_dictionary['R'] = str("{:.2f}".format(i_r))
            i_dictionary['RR'] = 'true'

        # i_rr = getattr(i, 'I-RR', None)
        # if i_rr:
        #     i_dictionary['RR'] = 'true'

        i_pb = str(
            "{:.2f}".format(getattr(i, 'price_subtotal') * coff * currency_rate))  # data['company_id']['vat_rate']
        if i_pb:
            i_dictionary['PB'] = i_pb  # TODO PB (Price Before VAT)

        # Getting tax percent if tax in line
        if tax_ids:
            rate = tax_ids.amount
        else:
            rate = 0
        is_exempt = False

        if i.tax_ids.amount == 0:
            if data["is_export"]:
                # i_ex = getattr(i, 'I-EX', None)
                # if i_ex:
                i_dictionary['EX'] = "EXPORT_OF_GOODS"
            elif i.tax_ids.exempt_code:
                i_dictionary['EX'] = i.tax_ids.exempt_code
                is_exempt = True

        i_vr = str("{:.2f}".format(rate))  # data['company_id']['vat_rate']
        if i_vr and not is_exempt:
            i_dictionary['VR'] = i_vr

        i_va = str(
            "{:.2f}".format(
                getattr(i, 'price_subtotal') * (rate / 100) * coff * currency_rate))  # data['company_id']['vat_rate']
        if i_va and not is_exempt:
            i_dictionary['VA'] = i_va

        i_in = getattr(i, 'I-IN', None)
        if i_in:
            i_dictionary['IN'] = str(i_in)

        i_pa = str(
            "{:.2f}".format(
                (getattr(i, 'price_subtotal') + (getattr(i, 'price_subtotal') * (rate / 100))) * coff * currency_rate))
        if i_pa:
            i_dictionary['PA'] = i_pa

        # Invoice->Items->I->VS
        # Invoice->Items->I->VS->VD
        # vd_d = getattr(i, 'VD-D', None)
        # if (vd_d):
        #     vd_dictionary['D'] = str(vd_d)
        #
        # vd_n = getattr(i, 'VD-N', None)
        # if (vd_n):
        #     vd_dictionary['N'] = str(vd_n)

        # Invoice->Items->I->VS->VN
        # Invoice->Items->I->VS->VN->V
        # v_num = getattr(i, 'V-Num', None)
        # if (v_num):
        #     v_dictionary['Num'] = str(v_num)

        list_i_dictionaries.append((i_dictionary, vd_dictionary, v_dictionary))

    # Invoice->SameTaxes
    # Invoice->SameTaxes->SameTax
    same_taxes_list = []
    # tax_line_ids = []
    if not data["is_export"] and invoice_is_issuer_in_vat:
        tax_line_ids = data['tax_line_ids']
        print("tax_line_ids", tax_line_ids)
        for tax_line in tax_line_ids:
            same_tax_item_count = 0
            same_tax_price_before_vat = 0
            invoice_line_ids = data['invoice_line_ids'].filtered(lambda inv_line: not inv_line.display_type)

            for invoice_line in invoice_line_ids:
                print("invoice_line.tax_ids", invoice_line.tax_ids)
                print("tax_line.tax_id", tax_line.tax_id)
                if invoice_line.tax_ids.id == tax_line.tax_id.id:
                    same_tax_item_count += 1
                    same_tax_price_before_vat += invoice_line.price_subtotal

            same_tax_dict = {
                "NumOfItems": str(same_tax_item_count),
                "PriceBefVAT": str("{:.2f}".format(float(same_tax_price_before_vat) * coff * data['currency_rate'])),
                "VATRate": "{:.2f}".format(float(tax_line.tax_id.amount)),
                "VATAmt": "{:.2f}".format(float(tax_line.amount_total * coff * data['currency_rate']))
            }
            exempt = None
            if tax_line.tax_id.exempt_code == "TYPE_1":
                exempt = "TYPE_1"
            elif tax_line.tax_id.exempt_code == "TYPE_2":
                exempt = "TYPE_2"
            if exempt:
                same_tax_dict.update(ExemptFromVAT=exempt)
                if "VATRate" in same_tax_dict:
                    del same_tax_dict["VATRate"]
                if "VATAmt" in same_tax_dict:
                    del same_tax_dict["VATAmt"]
            same_taxes_list.append(same_tax_dict)

        #   Company is Vat register so add same tax to empty tax lines
        invoice_line_with_no_tax_ids = data['invoice_line_ids'].filtered(
            lambda inv_line: not inv_line.display_type and not inv_line.tax_ids)
        if invoice_line_with_no_tax_ids:
            no_tax_line_total = sum(invoice_line_with_no_tax_ids.mapped("price_subtotal"))
            no_tax_line_count = len(invoice_line_with_no_tax_ids)
            have_no_tax_line = False
            for same_tax in same_taxes_list:
                if same_tax['VATRate'] == "0.00":
                    same_tax["NumOfItems"] = str(int(same_tax["NumOfItems"]) + no_tax_line_count)
                    same_tax["PriceBefVAT"] = "{:.2f}".format(float(same_tax["PriceBefVAT"]) + (
                            no_tax_line_total * coff * data['currency_rate']))
                    have_no_tax_line = True
                    break
            if not have_no_tax_line:
                same_taxes_list.append({
                    "NumOfItems": str(no_tax_line_count),
                    "PriceBefVAT": str("{:.2f}".format(float(no_tax_line_total) * coff * data['currency_rate'])),
                    "VATRate": "0.00",
                    "VATAmt": "0.00",
                })

    # sametax_num_of_items = data.get('invoice_same_tax_number_of_items')
    # if sametax_num_of_items:
    #     sametax_dictionary['NumOfItems'] = sametax_num_of_items
    #
    # sametax_price_bef_vat = data.get('invoice_same_tax_price_before_vat')
    # if (sametax_price_bef_vat):
    #     sametax_dictionary['PriceBefVAT'] = sametax_price_bef_vat
    #
    # sametax_vat_rate = data.get('invoice_same_tax_vat_rate')
    # if (sametax_vat_rate):
    #     sametax_dictionary['VATRate'] = sametax_vat_rate
    #
    # sametax_exempt_from_vat = data.get('invoice_same_tax_type_of_exempt_from_vat')
    # if (sametax_exempt_from_vat):
    #     sametax_dictionary['ExemptFromVAT'] = sametax_exempt_from_vat
    #
    # sametax_vat_amt = data.get('invoice_same_tax_vat_amount')
    # if (sametax_vat_amt):
    #     sametax_dictionary['VATAmt'] = sametax_vat_amt

    # Invoice->ConsTaxes
    # Invoice->ConsTaxes->ConsTax
    # constax_num_of_items = data.get('ConsTax-NumOfItems')
    # if (constax_num_of_items):
    #     constax_dictionary['NumOfItems'] = constax_num_of_items
    #
    # constax_price_bef_cons_tax = data.get('ConsTax-PriceBefConsTax')
    # if (constax_price_bef_cons_tax):
    #     constax_dictionary['PriceBefConsTax'] = constax_price_bef_cons_tax
    #
    # constax_cons_tax_rate = data.get('ConsTax-ConsTaxRate')
    # if (constax_cons_tax_rate):
    #     constax_dictionary['ConsTaxRate'] = constax_cons_tax_rate
    #
    # constax_cons_tax_amt = data.get('ConsTax-ConsTaxAmt')
    # if (constax_cons_tax_amt):
    #     constax_dictionary['ConsTaxAmt'] = constax_cons_tax_amt

    # Invoice->Fees
    # Invoice->Fees->Fee
    # fee_type = data.get('Fee-Type')
    # if (fee_type):
    #     fee_dictionary['Type'] = fee_type
    #
    # fee_amt = data.get('Fee-Amt')
    # if (fee_amt):
    #     fee_dictionary['Amt'] = fee_amt

    SubElement(xml_root, 'Header', header_dictionary)
    # print("invoice_dictionary", invoice_dictionary)
    invoice_subelement = SubElement(xml_root, 'Invoice', invoice_dictionary)
    if len(correctiveinv_dictionary) != 0:
        SubElement(invoice_subelement, 'CorrectiveInv',
                   correctiveinv_dictionary)
    if len(baddebtinv_dictionary) != 0:
        SubElement(invoice_subelement, 'BadDebtInv', baddebtinv_dictionary)

    # if (len(suminviicref_dictionary) != 0):
    #     suminviicrefs_subelement = SubElement(invoice_subelement,
    #                                           'SumInvIICRefs')
    #     SubElement(suminviicrefs_subelement, 'SumInvIICRef',
    #                suminviicref_dictionary)

    if (len(supplydateorperiod_dictionary) != 0):
        SubElement(invoice_subelement, 'SupplyDateOrPeriod',
                   supplydateorperiod_dictionary)

    paymethods_subelement = SubElement(invoice_subelement, 'PayMethods')
    paymethod_subelement = SubElement(paymethods_subelement, 'PayMethod',
                                      paymethod_dictionary)

    # if (len(voucher_dictionary) != 0):
    #     vouchers_subelement = SubElement(paymethod_subelement, 'Vouchers')
    #     SubElement(vouchers_subelement, 'Voucher', voucher_dictionary)

    if len(currency_dictionary) != 0:
        SubElement(invoice_subelement, 'Currency', currency_dictionary)

    SubElement(invoice_subelement, 'Seller', seller_dictionary)

    if len(buyer_dictionary) != 0:
        SubElement(invoice_subelement, 'Buyer', buyer_dictionary)

    items_subelement = SubElement(invoice_subelement, 'Items')
    for i_dictionary, vd_dictionary, v_dictionary in list_i_dictionaries:
        i_subelement = SubElement(items_subelement, 'I', i_dictionary)

        # if (len(vd_dictionary) != 0 & len(v_dictionary) != 0):
        #     vs_subelement = SubElement(i_subelement, 'VS')
        #     if (len(vd_dictionary) != 0):
        #         SubElement(vs_subelement, 'VD', vd_dictionary)
        #     if (len(v_dictionary) != 0):
        #         vn_subelement = SubElement(vs_subelement, 'VN')
        #         SubElement(vn_subelement, 'V', v_dictionary)

    # if sametax_dictionary:
    #     sametaxes_subelement = SubElement(invoice_subelement, 'SameTaxes')
    #     SubElement(sametaxes_subelement, 'SameTax', sametax_dictionary)

    if same_taxes_list:
        same_taxes_sub_element = SubElement(invoice_subelement, 'SameTaxes')
        for same_tax in same_taxes_list:
            # print("Same>>>>>>>", same_tax)
            SubElement(same_taxes_sub_element, 'SameTax', same_tax)
    #
    # if (len(constax_dictionary) != 0):
    #     constaxes_subelement = SubElement(invoice_subelement, 'ConsTaxes')
    #     SubElement(constaxes_subelement, 'ConsTax', constax_dictionary)
    #
    # if (len(fee_dictionary) != 0):
    #     fees_subelement = SubElement(invoice_subelement, 'Fees')
    #     SubElement(fees_subelement, 'Fee', fee_dictionary)

    signed_root = tostring(sign_xml(xml_root, company_p12_certificate=company_p12_certificate,
                                    certificate_password=certificate_password))
    final_xml = envelope_start + signed_root.decode('utf-8') + envelope_end

    return final_xml
