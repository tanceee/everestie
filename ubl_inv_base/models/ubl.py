import logging

from lxml import etree

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_round

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.generic import NameObject
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BaseUbl(models.AbstractModel):
    _name = 'base.ubl'
    _description = 'Common methods to generate and parse UBL XML files'

    # ==================== METHODS TO GENERATE UBL files

    def _ubl_add_payment_means(self, partner_bank, payment_mode, date_due, parent_node, ns, payment_identifier=None,
                               version='2.1'):
        pay_means = etree.SubElement(parent_node, ns['cac'] + 'PaymentMeans')
        pay_means_code = etree.SubElement(pay_means, ns['cbc'] + 'PaymentMeansCode')
        pay_means_code.text = '42'  # TODO Updated when needed

        # Why not schemeAgencyID='6' + schemeID
        # if payment_mode:  # type is a required field on payment_mode
        #     if not payment_mode.payment_method_id.unece_id:
        #         raise UserError(_(
        #             "Missing 'UNECE Payment Mean' on payment type '%s' "
        #             "used by the payment mode '%s'.") % (
        #                             payment_mode.payment_method_id.name, payment_mode.name))
        #     pay_means_code.text = payment_mode.payment_method_id.unece_code
        # else:
        #     pay_means_code.text = '31'
        #     logger.warning(
        #         'Missing payment mode on invoice ID %d. '
        #         'Using 31 (wire transfer) as UNECE code as fallback '
        #         'for payment mean', self.id)
        # if date_due:
        #     pay_due_date = etree.SubElement(
        #         pay_means, ns['cbc'] + 'PaymentDueDate')
        #     pay_due_date.text = date_due.strftime('%Y-%m-%d')
        if pay_means_code.text in ['30', '31', '42']:
            if (not partner_bank and
                    payment_mode and
                    payment_mode.bank_account_link == 'fixed' and
                    payment_mode.fixed_journal_id):
                partner_bank = payment_mode.fixed_journal_id.bank_account_id
            if partner_bank and partner_bank.acc_type == 'iban':
                # In the Chorus specs, they except 'IBAN' in PaymentChannelCode
                # I don't know if this usage is common or not
                # payment_channel_code = etree.SubElement(
                #     pay_means, ns['cbc'] + 'PaymentChannelCode')
                # payment_channel_code.text = 'IBAN'
                if payment_identifier:
                    payment_id = etree.SubElement(
                        pay_means, ns['cbc'] + 'PaymentID')
                    payment_id.text = payment_identifier
                payee_fin_account = etree.SubElement(
                    pay_means, ns['cac'] + 'PayeeFinancialAccount')
                payee_fin_account_id = etree.SubElement(
                    payee_fin_account, ns['cbc'] + 'ID', schemeName='IBAN')
                payee_fin_account_id.text = \
                    partner_bank.sanitized_acc_number
                if not partner_bank.bank_id:
                    raise ValidationError("Setup the bank account!")
                payee_fin_bank_name = etree.SubElement(
                    payee_fin_account,
                    ns['cbc'] + 'Name')
                curr_code = ""
                if partner_bank.currency_id:
                    curr_code = "-" + partner_bank.currency_id.name
                payee_fin_bank_name.text = partner_bank.partner_id.name + curr_code

                if partner_bank.bank_bic:
                    financial_inst_branch = etree.SubElement(
                        payee_fin_account,
                        ns['cac'] + 'FinancialInstitutionBranch')
                    # financial_inst = etree.SubElement(
                    #     financial_inst_branch,
                    #     ns['cac'] + 'FinancialInstitution')
                    financial_inst_id = etree.SubElement(
                        financial_inst_branch, ns['cbc'] + 'ID', schemeName='BIC')
                    financial_inst_id.text = partner_bank.bank_bic

    @api.model
    def _ubl_add_country(self, country, parent_node, ns, version='2.1'):
        country_root = etree.SubElement(parent_node, ns['cac'] + 'Country')
        country_code = etree.SubElement(
            country_root, ns['cbc'] + 'IdentificationCode')
        country_code.text = country.code
        # country_name = etree.SubElement(
        #     country_root, ns['cbc'] + 'Name')
        # country_name.text = country.name

    @api.model
    def _ubl_add_address(self, partner, node_name, parent_node, ns, version='2.1'):
        address = etree.SubElement(parent_node, ns['cac'] + node_name)
        if partner.street:
            streetname = etree.SubElement(
                address, ns['cbc'] + 'StreetName')
            streetname.text = partner.street
        if partner.street2:
            addstreetname = etree.SubElement(address, ns['cbc'] + 'AdditionalStreetName')
            addstreetname.text = partner.street2
        if hasattr(partner, 'street3') and partner.street3:
            blockname = etree.SubElement(
                address, ns['cbc'] + 'BlockName')
            blockname.text = partner.street3
        if partner.city:
            city = etree.SubElement(address, ns['cbc'] + 'CityName')
            city.text = partner.city
        if partner.zip:
            zip = etree.SubElement(address, ns['cbc'] + 'PostalZone')
            zip.text = partner.zip
        if partner.state_id:
            state = etree.SubElement(
                address, ns['cbc'] + 'CountrySubentity')
            state.text = partner.state_id.name
            # state_code = etree.SubElement(
            #     address, ns['cbc'] + 'CountrySubentityCode')
            # state_code.text = partner.state_id.code
        if partner.country_id:
            self._ubl_add_country(partner.country_id, address, ns, version=version)
        else:
            logger.warning('UBL: missing country on partner %s', partner.name)

    @api.model
    def _ubl_get_contact_id(self, partner):
        return False

    @api.model
    def _ubl_add_contact(self, partner, parent_node, ns, node_name='Contact', version='2.1'):
        contact = etree.SubElement(parent_node, ns['cac'] + node_name)
        contact_id_text = self._ubl_get_contact_id(partner)
        if contact_id_text:
            contact_id = etree.SubElement(contact, ns['cbc'] + 'ID')
            contact_id.text = contact_id_text
        if partner.parent_id:
            contact_name = etree.SubElement(contact, ns['cbc'] + 'Name')
            contact_name.text = partner.name
        phone = partner.phone or partner.commercial_partner_id.phone
        if phone:
            telephone = etree.SubElement(contact, ns['cbc'] + 'Telephone')
            telephone.text = phone
        email = partner.email or partner.commercial_partner_id.email
        if email:
            electronicmail = etree.SubElement(
                contact, ns['cbc'] + 'ElectronicMail')
            electronicmail.text = email

    # @api.model
    # def _ubl_add_language(self, lang_code, parent_node, ns, version='2.1'):
    #     langs = self.env['res.lang'].search([('code', '=', lang_code)])
    #     if not langs:
    #         return
    #     lang = langs[0]
    #     lang_root = etree.SubElement(parent_node, ns['cac'] + 'Language')
    #     lang_name = etree.SubElement(lang_root, ns['cbc'] + 'Name')
    #     lang_name.text = lang.name
    #     lang_code = etree.SubElement(lang_root, ns['cbc'] + 'LocaleCode')
    #     lang_code.text = lang.code

    @api.model
    def _ubl_get_party_identification(self, commercial_partner):
        '''This method is designed to be inherited in localisation modules
        Should return a dict with key=SchemeName, value=Identifier'''
        return {}

    @api.model
    def _ubl_add_party_identification(self, commercial_partner, parent_node, ns, version='2.1'):
        id_dict = self._ubl_get_party_identification(commercial_partner)
        if id_dict:
            party_identification = etree.SubElement(
                parent_node, ns['cac'] + 'PartyIdentification')
            for scheme_name, party_id_text in id_dict.items():
                party_identification_id = etree.SubElement(
                    party_identification, ns['cbc'] + 'ID',
                    schemeName=scheme_name)
                party_identification_id.text = party_id_text
        return

    @api.model
    def _ubl_get_tax_scheme_dict_from_partner(self, commercial_partner):
        # if commercial_partner.country_id.code=="AL":
        if self.invoice_line_ids:
            lines_with_tax = self.invoice_line_ids.filtered(
                lambda line: line.tax_ids and not line.display_type)
            if lines_with_tax:
                tax_scheme_dict = {
                    'id': 'VAT',
                    'name': False,
                    'type_code': False,
                }
            else:
                tax_scheme_dict = {
                    'id': 'FRE',
                    'name': False,
                    'type_code': False,
                }
            return tax_scheme_dict
        # else:
        #     tax_scheme_dict = {
        #         'id': 'FRE',
        #         'name': False,
        #         'type_code': False,
        #     }
        #     return tax_scheme_dict

    @api.model
    def _ubl_add_party_tax_scheme(
            self, commercial_partner, parent_node, ns, version='2.1'):
        if commercial_partner.vat:
            party_tax_scheme = etree.SubElement(parent_node, ns['cac'] + 'PartyTaxScheme')
            # registration_name = etree.SubElement(party_tax_scheme, ns['cbc'] + 'RegistrationName')
            # registration_name.text = commercial_partner.name

            company_id = etree.SubElement(party_tax_scheme, ns['cbc'] + 'CompanyID')
            company_id.text = commercial_partner.country_id.code + "" + commercial_partner.sanitized_vat

            tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_partner(commercial_partner)
            self._ubl_add_tax_scheme(tax_scheme_dict, party_tax_scheme, ns, version=version)

    @api.model
    def _ubl_add_party_legal_entity(self, commercial_partner, parent_node, ns, version='2.1'):
        party_legal_entity = etree.SubElement(parent_node, ns['cac'] + 'PartyLegalEntity')
        registration_name = etree.SubElement(party_legal_entity, ns['cbc'] + 'RegistrationName')
        registration_name.text = commercial_partner.name

        company_id = etree.SubElement(party_legal_entity, ns['cbc'] + 'CompanyID')
        company_id.text = commercial_partner.sanitized_vat
        # self._ubl_add_address(
        #     commercial_partner, 'RegistrationAddress', party_legal_entity,
        #     ns, version=version)

    @api.model
    def _ubl_add_party_sup(self, partner, company, node_name, parent_node, ns, version='2.1'):
        commercial_partner = partner.commercial_partner_id
        # print("commercial_partner", commercial_partner)
        party = etree.SubElement(parent_node, ns['cac'] + node_name)
        # if commercial_partner.website:
        #     website = etree.SubElement(party, ns['cbc'] + 'WebsiteURI')
        #     website.text = commercial_partner.website
        endpoint_id = etree.SubElement(party, ns['cbc'] + 'EndpointID')
        endpoint_id.text = partner.vat
        endpoint_id.set('schemeID', '9923')  # TODO 	Seller electronic address identification scheme identifier
        # self._ubl_add_party_identification(commercial_partner, party, ns, version=version)

        party_name = etree.SubElement(party, ns['cac'] + 'PartyName')
        name = etree.SubElement(party_name, ns['cbc'] + 'Name')
        name.text = commercial_partner.name

        # if partner.lang:
        #     self._ubl_add_language(partner.lang, party, ns, version=version)
        self._ubl_add_address(commercial_partner, 'PostalAddress', party, ns, version=version)
        self._ubl_add_party_tax_scheme(commercial_partner, party, ns, version=version)
        if company:
            self._ubl_add_party_legal_entity(commercial_partner, party, ns, version='2.1')
        self._ubl_add_contact(partner, party, ns, version=version)

    @api.model
    def _ubl_add_party_buy(self, partner, company, node_name, parent_node, ns, version='2.1'):
        commercial_partner = partner.commercial_partner_id
        party = etree.SubElement(parent_node, ns['cac'] + node_name)
        # if commercial_partner.website:
        #     website = etree.SubElement(party, ns['cbc'] + 'WebsiteURI')
        #     website.text = commercial_partner.website
        # self._ubl_add_party_identification(commercial_partner, party, ns, version=version)
        endpoint_id = etree.SubElement(party, ns['cbc'] + 'EndpointID')
        endpoint_id.text = partner.vat
        endpoint_id.set('schemeID', '9923')  # TODO 	Seller electronic address identification scheme identifier

        party_name = etree.SubElement(party, ns['cac'] + 'PartyName')
        name = etree.SubElement(party_name, ns['cbc'] + 'Name')
        name.text = commercial_partner.name

        # if partner.lang:
        #     self._ubl_add_language(partner.lang, party, ns, version=version)
        self._ubl_add_address(commercial_partner, 'PostalAddress', party, ns, version=version)
        print("commercial_partner", commercial_partner)
        print("party", party)
        self._ubl_add_party_tax_scheme(commercial_partner, party, ns, version=version)
        # if company: # TODO Check company for buyer
        self._ubl_add_party_legal_entity(commercial_partner, party, ns, version='2.1')
        self._ubl_add_contact(partner, party, ns, version=version)

    @api.model
    def _ubl_invoice_period(self, start_date, end_date, node_name, parent_node, ns, version='2.1'):
        if start_date and end_date:
            invoice_period_root = etree.SubElement(parent_node, ns['cac'] + node_name)
            start_date_node = etree.SubElement(invoice_period_root, ns['cbc'] + "StartDate")
            start_date_node.text = start_date.strftime('%Y-%m-%d')
            end_date_node = etree.SubElement(invoice_period_root, ns['cbc'] + "EndDate")
            end_date_node.text = end_date.strftime('%Y-%m-%d')

    @api.model
    def _ubl_add_customer_party(self, partner, company, node_name, parent_node, ns, version='2.1'):
        """Please read the docstring of the method _ubl_add_supplier_party"""
        if company:
            if partner:
                # print("partner.commercial_partner_id", partner.commercial_partner_id)
                # print("company.partner_id", company.partner_id)
                assert partner.commercial_partner_id.id == company.partner_id.id, 'partner is wrong'
            else:
                partner = company.partner_id
        customer_party_root = etree.SubElement(parent_node, ns['cac'] + node_name)
        # if not company and partner.commercial_partner_id.ref:
        #     customer_ref = etree.SubElement(
        #         customer_party_root, ns['cbc'] + 'SupplierAssignedAccountID')
        #     customer_ref.text = partner.commercial_partner_id.ref
        self._ubl_add_party_buy(partner, company, 'Party', customer_party_root, ns, version=version)
        # TODO: rewrite support for AccountingContact + add DeliveryContact
        # Additional optional args
        if partner and not company and partner.parent_id:
            self._ubl_add_contact(
                partner, customer_party_root, ns,
                node_name='AccountingContact', version=version)

    @api.model
    def _ubl_add_supplier_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        """The company argument has been added to properly handle the
        'ref' field.
        In Odoo, we only have one ref field, in which we are supposed
        to enter the reference that our company gives to its
        customers/suppliers. We unfortunately don't have a native field to
        enter the reference that our suppliers/customers give to us.
        So, to set the fields CustomerAssignedAccountID and
        SupplierAssignedAccountID, I need to know if the partner for
        which we want to build the party block is our company or a
        regular partner:
        1) if it is a regular partner, call the method that way:
            self._ubl_add_supplier_party(partner, False, ...)
        2) if it is our company, call the method that way:
            self._ubl_add_supplier_party(False, company, ...)
        """
        if company:
            if partner:
                assert partner.commercial_partner_id == company.partner_id, 'partner is wrong'
            else:
                partner = company.partner_id
        supplier_party_root = etree.SubElement(parent_node, ns['cac'] + node_name)
        # if not company and partner.commercial_partner_id.ref:
        #     supplier_ref = etree.SubElement(
        #         supplier_party_root, ns['cbc'] + 'CustomerAssignedAccountID')
        #     supplier_ref.text = partner.commercial_partner_id.ref
        self._ubl_add_party_sup(partner, company, 'Party', supplier_party_root, ns, version=version)

    @api.model
    def _ubl_despatch_document_reference(self, despatch_document_reference, node_name, parent_node, ns, version='2.1'):
        despatch_document_reference_root = etree.SubElement(parent_node, ns['cac'] + node_name)
        ref_id = etree.SubElement(despatch_document_reference_root, ns['cbc'] + 'ID')
        ref_id.text = despatch_document_reference

    @api.model
    def _ubl_add_additional_doc_ref(self, attach_doc_id, node_name, parent_node, ns, version='2.1'):
        file_name = attach_doc_id.name
        mime_type = attach_doc_id.mimetype
        file_binary = attach_doc_id.datas
        additional_document_reference_root = etree.SubElement(parent_node, ns['cac'] + node_name)
        doc_id = etree.SubElement(additional_document_reference_root, ns['cbc'] + 'ID')
        doc_id.text = "1_101"  # TODO Use dynamic ID

        attachment_root = etree.SubElement(additional_document_reference_root, ns['cac'] + 'Attachment')
        binary_object_element = etree.SubElement(attachment_root, ns['cbc'] + 'EmbeddedDocumentBinaryObject',
                                                 mimeCode=mime_type, filename=file_name)
        binary_object_element.text = file_binary
        print("additional_document_reference_root", etree.tostring(additional_document_reference_root, encoding='utf-8', method='xml'))\

    @api.model
    def _ubl_add_additional_doc_ref_links(self, attach_doc_link_id, node_name, parent_node, ns, version='2.1'):
        additional_document_reference_root = etree.SubElement(parent_node, ns['cac'] + node_name)
        doc_id = etree.SubElement(additional_document_reference_root, ns['cbc'] + 'ID')
        doc_id.text = "1_102"  # TODO Use dynamic ID

        doc_description = etree.SubElement(additional_document_reference_root, ns['cbc'] + 'DocumentDescription')
        doc_description.text = attach_doc_link_id.name

        attachment_root = etree.SubElement(additional_document_reference_root, ns['cac'] + 'Attachment')
        external_ref_element = etree.SubElement(attachment_root, ns['cac'] + 'ExternalReference')
        uri_element = etree.SubElement(external_ref_element, ns['cbc'] + 'URI')
        uri_element.text = attach_doc_link_id.link
        # print("additional_document_reference_root", etree.tostring(additional_document_reference_root, encoding='utf-8', method='xml'))

    # @api.model
    # def _ubl_add_delivery(
    #         self, delivery_partner, parent_node, ns, version='2.1'):
    #     delivery = etree.SubElement(parent_node, ns['cac'] + 'Delivery')
    #     delivery_location = etree.SubElement(
    #         delivery, ns['cac'] + 'DeliveryLocation')
    #     self._ubl_add_address(
    #         delivery_partner, 'Address', delivery_location, ns,
    #         version=version)
    #     self._ubl_add_party(
    #         delivery_partner, False, 'DeliveryParty', delivery, ns,
    #         version=version)

    @api.model
    def _ubl_add_delivery_terms(
            self, incoterm, parent_node, ns, version='2.1'):
        delivery_term = etree.SubElement(
            parent_node, ns['cac'] + 'DeliveryTerms')
        delivery_term_id = etree.SubElement(
            delivery_term, ns['cbc'] + 'ID',
            schemeAgencyID='6', schemeID='INCOTERM')
        delivery_term_id.text = incoterm.code

    @api.model
    def _ubl_add_payment_terms(
            self, payment_term, parent_node, ns, version='2.1'):
        pay_term_root = etree.SubElement(
            parent_node, ns['cac'] + 'PaymentTerms')
        pay_term_note = etree.SubElement(
            pay_term_root, ns['cbc'] + 'Note')
        pay_term_note.text = payment_term.name

    @api.model
    def _ubl_add_line_item(
            self, line_number, name, product, type, quantity, uom, parent_node,
            ns, seller=False, currency=False, price_subtotal=False,
            qty_precision=3, price_precision=2, version='2.1'):
        line_item = etree.SubElement(
            parent_node, ns['cac'] + 'LineItem')
        line_item_id = etree.SubElement(line_item, ns['cbc'] + 'ID')
        line_item_id.text = str(line_number)
        if not uom.unece_code:
            raise UserError(_(
                "Missing UNECE code on unit of measure '%s'")
                            % uom.name)
        quantity_node = etree.SubElement(
            line_item, ns['cbc'] + 'Quantity',
            unitCode=uom.unece_code)
        quantity_node.text = str(quantity)
        if currency and price_subtotal:
            line_amount = etree.SubElement(
                line_item, ns['cbc'] + 'LineExtensionAmount',
                currencyID=currency.name)
            line_amount.text = str(price_subtotal)
            price_unit = 0.0
            # Use price_subtotal/qty to compute price_unit to be sure
            # to get a *tax_excluded* price unit
            if not float_is_zero(quantity, precision_digits=qty_precision):
                price_unit = float_round(
                    price_subtotal / float(quantity),
                    precision_digits=price_precision)
            price = etree.SubElement(
                line_item, ns['cac'] + 'Price')
            price_amount = etree.SubElement(
                price, ns['cbc'] + 'PriceAmount',
                currencyID=currency.name)
            price_amount.text = str(price_unit)
            base_qty = etree.SubElement(
                price, ns['cbc'] + 'BaseQuantity',
                unitCode=uom.unece_code)
            base_qty.text = '1'  # What else could it be ?
        # print("UBL add Item>>>>>>>>>>>>", product, type)
        self._ubl_add_item(
            name, product, line_item, ns, type=type, seller=seller,
            version=version)

    @api.model
    def _ubl_add_item(
            self, line_id, name, product, parent_node, ns, type='purchase',
            seller=False, version='2.1'):
        """Beware that product may be False (in particular on invoices)"""
        assert type in ('sale', 'purchase'), 'Wrong type param'
        assert name, 'name is a required arg'
        item = etree.SubElement(parent_node, ns['cac'] + 'Item')
        product_name = False
        seller_code = False
        # if product:
            # if type == 'purchase':
            #     if seller:
            #         sellers = product._select_seller(
            #             partner_id=seller, quantity=0.0, date=None,
            #             uom_id=False)
            #         if sellers:
            #             product_name = sellers[0].product_name
            #             seller_code = sellers[0].product_code
            # if not seller_code:
            #     seller_code = product.default_code
            # if not product_name:
            #     variant = ", ".join(
            #         [v.name for v in product.attribute_value_ids])
            #     product_name = variant and "%s (%s)" % (product.name, variant) \
            #                    or product.name
        description = etree.SubElement(item, ns['cbc'] + 'Description')
        description.text = name
        name_node = etree.SubElement(item, ns['cbc'] + 'Name')
        name_node.text = name
        # name_node.text = product_name or name.split('\n')[0]
        # if seller_code:
        #     seller_identification = etree.SubElement(
        #         item, ns['cac'] + 'SellersItemIdentification')
        #     seller_identification_id = etree.SubElement(
        #         seller_identification, ns['cbc'] + 'ID')
        #     seller_identification_id.text = seller_code
        if product:
            # if product.barcode:
            #     std_identification = etree.SubElement(
            #         item, ns['cac'] + 'StandardItemIdentification')
            #     std_identification_id = etree.SubElement(
            #         std_identification, ns['cbc'] + 'ID',
            #         schemeAgencyID='6', schemeID='GTIN')
            #     std_identification_id.text = product.barcode
            # I'm not 100% sure, but it seems that ClassifiedTaxCategory
            # contains the taxes of the product without taking into
            # account the fiscal position
            taxes = None
            if type == 'sale':
                # taxes = product.taxes_id
                taxes = line_id.tax_ids
            # else:
            #     taxes = product.supplier_taxes_id

            # print("TAXES @@@@@@@@@@@", taxes)
            if taxes:
                for tax in taxes.filtered(lambda t: t.company_id == self.env.user.company_id):
                    self._ubl_add_tax_category(tax, item, ns, node_name='ClassifiedTaxCategory', version=version)
            else:
                tax_category = etree.SubElement(item, ns['cac'] + 'ClassifiedTaxCategory')
                # if not tax.unece_categ_id:
                #     raise UserError(_(
                #         "Missing UNECE Tax Category on tax '%s'" % tax.name))
                tax_category_id = etree.SubElement(tax_category, ns['cbc'] + 'ID')
                tax_category_id.text = "O"

                # tax_name = etree.SubElement(
                #     tax_category, ns['cbc'] + 'Name')
                # tax_name.text = tax.name
                # if tax.amount_type == 'percent':
                # tax_percent = etree.SubElement(
                #     tax_category, ns['cbc'] + 'Percent')
                # tax_percent.text = '%0.*f' % (2, 0)  # str(tax.amount)
                # tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
                # self._ubl_add_tax_scheme(tax_scheme_dict, tax_category, ns, version=version)

                tax_scheme = etree.SubElement(tax_category, ns['cac'] + 'TaxScheme')
                # if tax_scheme_dict.get('id'):
                tax_scheme_id = etree.SubElement(tax_scheme, ns['cbc'] + 'ID')
                tax_scheme_id.text = "VAT"

            # for attribute_value in product.attribute_value_ids:
            #     item_property = etree.SubElement(
            #         item, ns['cac'] + 'AdditionalItemProperty')
            #     property_name = etree.SubElement(
            #         item_property, ns['cbc'] + 'Name')
            #     property_name.text = attribute_value.attribute_id.name
            #     property_value = etree.SubElement(
            #         item_property, ns['cbc'] + 'Value')
            #     property_value.text = attribute_value.name

    @api.model
    def _ubl_add_tax_subtotal(self, taxable_amount, tax_amount, tax, currency_code, parent_node, ns, version='2.1'):
        prec = self.env['decimal.precision'].precision_get('Account')
        tax_subtotal = etree.SubElement(parent_node, ns['cac'] + 'TaxSubtotal')
        # print("self.move_type", self.move_type, taxable_amount, prec)

        if not float_is_zero(taxable_amount, precision_digits=prec) or self.tax_line_ids:
            taxable_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxableAmount', currencyID=currency_code)
            if self.move_type == 'out_invoice':
                taxable_amount_node.text = '%0.*f' % (2, taxable_amount)
            elif self.move_type == 'out_refund':
                taxable_amount_node.text = '%0.*f' % (2, taxable_amount * -1)

        tax_amount_node = etree.SubElement(tax_subtotal, ns['cbc'] + 'TaxAmount', currencyID=currency_code)
        if self.move_type == 'out_invoice':
            tax_amount_node.text = '%0.*f' % (2, tax_amount)
        elif self.move_type == 'out_refund':
            tax_amount_node.text = '%0.*f' % (2, tax_amount * -1)

        # if tax.amount_type == 'percent' and not float_is_zero(tax.amount, precision_digits=prec + 3):
        #     percent = etree.SubElement(tax_subtotal, ns['cbc'] + 'Percent')
        #     percent.text = str(float_round(tax.amount, precision_digits=2))
        self._ubl_add_tax_category(tax, tax_subtotal, ns, version=version)

    @api.model
    def _ubl_add_tax_category(self, tax, parent_node, ns, node_name='TaxCategory', version='2.1'):
        tax_category = etree.SubElement(parent_node, ns['cac'] + node_name)
        if not tax.unece_categ_id:
            raise UserError(_(
                "Missing UNECE Tax Category on tax '%s'" % tax.name))
        tax_category_id = etree.SubElement(tax_category, ns['cbc'] + 'ID')
        tax_category_id.text = tax.unece_categ_code

        # tax_name = etree.SubElement(
        #     tax_category, ns['cbc'] + 'Name')
        # tax_name.text = tax.name
        if tax.amount_type == 'percent':
            tax_percent = etree.SubElement(
                tax_category, ns['cbc'] + 'Percent')
            tax_percent.text = '%0.*f' % (2, tax.amount)  # str(tax.amount)
        if tax.unece_categ_id.code == "E":  # and node_name=='TaxCategory'
            tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
            tax_percent.text = "VATEX-EU-132"
            tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReason')
            tax_percent.text = "Exempt based on article 132 of Council Directive 2006/112/EC"

        if tax.unece_categ_id.code == "G":  # and node_name=='TaxCategory'
            tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
            tax_percent.text = "VATEX-EU-G"
            tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReason')
            tax_percent.text = "Export outside the EU"

        # if tax.unece_categ_id.code == "Z":  # and node_name=='TaxCategory'
        #     tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReasonCode')
        #     tax_percent.text = tax.exempt_code
        #     tax_percent = etree.SubElement(tax_category, ns['cbc'] + 'TaxExemptionReason')
        #     tax_percent.text = tax.description_exempt
        tax_scheme_dict = self._ubl_get_tax_scheme_dict_from_tax(tax)
        self._ubl_add_tax_scheme(tax_scheme_dict, tax_category, ns, version=version)

    @api.model
    def _ubl_get_tax_scheme_dict_from_tax(self, tax):
        if not tax.unece_type_id:
            raise UserError(_(
                "Missing UNECE Tax Type on tax '%s'" % tax.name))
        tax_scheme_dict = {
            'id': tax.unece_type_code,
            'name': False,
            'type_code': False,
        }
        return tax_scheme_dict

    @api.model
    def _ubl_add_tax_scheme(self, tax_scheme_dict, parent_node, ns, version='2.1'):
        tax_scheme = etree.SubElement(parent_node, ns['cac'] + 'TaxScheme')
        if tax_scheme_dict.get('id'):
            tax_scheme_id = etree.SubElement(tax_scheme, ns['cbc'] + 'ID')
            tax_scheme_id.text = tax_scheme_dict['id']
            # tax_scheme_id.text = "FRE"  # TODO 23 JUL
        # if tax_scheme_dict.get('name'):
        #     tax_scheme_name = etree.SubElement(tax_scheme, ns['cbc'] + 'Name')
        #     tax_scheme_name.text = tax_scheme_dict['name']
        # if tax_scheme_dict.get('type_code'):
        #     tax_scheme_type_code = etree.SubElement(
        #         tax_scheme, ns['cbc'] + 'TaxTypeCode')
        #     tax_scheme_type_code.text = tax_scheme_dict['type_code']

    # @api.model
    # def _ubl_get_nsmap_namespace(self, doc_name, version='2.1'):
    #     nsmap = {
    #         None: 'urn:oasis:names:specification:ubl:schema:xsd:' + doc_name,
    #         'cac': 'urn:oasis:names:specification:ubl:'
    #                'schema:xsd:CommonAggregateComponents-2',
    #         'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:'
    #                'CommonBasicComponents-2',
    #         }
    #     ns = {
    #         'cac': '{urn:oasis:names:specification:ubl:schema:xsd:'
    #                'CommonAggregateComponents-2}',
    #         'cbc': '{urn:oasis:names:specification:ubl:schema:xsd:'
    #                'CommonBasicComponents-2}',
    #         }
    #     return nsmap, ns

    # @api.model
    # def _ubl_check_xml_schema(self, xml_string, document, version='2.1'):
    #     """Validate the XML file against the XSD"""
    #     xsd_file = 'base_ubl/data/xsd-%s/maindoc/UBL-%s-%s.xsd' % (
    #         version, document, version)
    #     xsd_etree_obj = etree.parse(file_open(xsd_file))
    #     official_schema = etree.XMLSchema(xsd_etree_obj)
    #     try:
    #         t = etree.parse(BytesIO(xml_string))
    #         official_schema.assertValid(t)
    #     except Exception as e:
    #         # if the validation of the XSD fails, we arrive here
    #         logger = logging.getLogger(__name__)
    #         logger.warning(
    #             "The XML file is invalid against the XML Schema Definition")
    #         logger.warning(xml_string)
    #         logger.warning(e)
    #         raise UserError(_(
    #             "The UBL XML file is not valid against the official "
    #             "XML Schema Definition. The XML file and the "
    #             "full error have been written in the server logs. "
    #             "Here is the error, which may give you an idea on the "
    #             "cause of the problem : %s.")
    #                         % str(e))
    #     return True

    # @api.model
    # def embed_xml_in_pdf(
    #         self, xml_string, xml_filename, pdf_content=None, pdf_file=None):
    #     """
    #     2 possible uses:
    #     a) use the pdf_content argument, which has the binary of the PDF
    #     -> it will return the new PDF binary with the embedded XML
    #     (used for qweb-pdf reports)
    #     b) OR use the pdf_file argument, which has the path to the
    #     original PDF file
    #     -> it will re-write this file with the new PDF
    #     (used for py3o reports, *_ubl_py3o modules in this repo)
    #     """
    #     assert pdf_content or pdf_file, 'Missing pdf_file or pdf_content'
    #     logger.debug('Starting to embed %s in PDF file', xml_filename)
    #     if pdf_file:
    #         original_pdf_file = pdf_file
    #     elif pdf_content:
    #         original_pdf_file = BytesIO(pdf_content)
    #     original_pdf = PdfFileReader(original_pdf_file)
    #     new_pdf_filestream = PdfFileWriter()
    #     new_pdf_filestream.appendPagesFromReader(original_pdf)
    #     new_pdf_filestream.addAttachment(xml_filename, xml_string)
    #     # show attachments when opening PDF
    #     new_pdf_filestream._root_object.update({
    #         NameObject("/PageMode"): NameObject("/UseAttachments"),
    #     })
    #     new_pdf_content = None
    #     if pdf_file:
    #         f = open(pdf_file, 'wb')
    #         new_pdf_filestream.write(f)
    #         f.close()
    #         new_pdf_content = pdf_content
    #     elif pdf_content:
    #         with NamedTemporaryFile(prefix='odoo-ubl-', suffix='.pdf') as f:
    #             new_pdf_filestream.write(f)
    #             f.seek(0)
    #             new_pdf_content = f.read()
    #             f.close()
    #     logger.info('%s file added to PDF', xml_filename)
    #     return new_pdf_content

    # ==================== METHODS TO PARSE UBL files

    # @api.model
    # def ubl_parse_customer_party(self, customer_party_node, ns):
    #     ref_xpath = customer_party_node.xpath(
    #         'cac:SupplierAssignedAccountID', namespaces=ns)
    #     party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
    #     partner_dict = self.ubl_parse_party(party_node, ns)
    #     partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
    #     return partner_dict

    # @api.model
    # def ubl_parse_supplier_party(self, customer_party_node, ns):
    #     ref_xpath = customer_party_node.xpath(
    #         'cac:CustomerAssignedAccountID', namespaces=ns)
    #     party_node = customer_party_node.xpath('cac:Party', namespaces=ns)[0]
    #     partner_dict = self.ubl_parse_party(party_node, ns)
    #     partner_dict['ref'] = ref_xpath and ref_xpath[0].text or False
    #     return partner_dict

    # @api.model
    # def ubl_parse_party(self, party_node, ns):
    #     partner_name_xpath = party_node.xpath(
    #         'cac:PartyName/cbc:Name', namespaces=ns)
    #     vat_xpath = party_node.xpath(
    #         'cac:PartyTaxScheme/cbc:CompanyID', namespaces=ns)
    #     email_xpath = party_node.xpath(
    #         'cac:Contact/cbc:ElectronicMail', namespaces=ns)
    #     phone_xpath = party_node.xpath(
    #         'cac:Contact/cbc:Telephone', namespaces=ns)
    #     website_xpath = party_node.xpath(
    #         'cbc:WebsiteURI', namespaces=ns)
    #     partner_dict = {
    #         'vat': vat_xpath and vat_xpath[0].text or False,
    #         'name': partner_name_xpath[0].text,
    #         'email': email_xpath and email_xpath[0].text or False,
    #         'website': website_xpath and website_xpath[0].text or False,
    #         'phone': phone_xpath and phone_xpath[0].text or False,
    #     }
    #     address_xpath = party_node.xpath('cac:PostalAddress', namespaces=ns)
    #     if address_xpath:
    #         address_dict = self.ubl_parse_address(address_xpath[0], ns)
    #         partner_dict.update(address_dict)
    #     return partner_dict

    # @api.model
    # def ubl_parse_address(self, address_node, ns):
    #     country_code_xpath = address_node.xpath(
    #         'cac:Country/cbc:IdentificationCode',
    #         namespaces=ns)
    #     country_code = country_code_xpath and country_code_xpath[0].text \
    #                    or False
    #     state_code_xpath = address_node.xpath(
    #         'cbc:CountrySubentityCode', namespaces=ns)
    #     state_code = state_code_xpath and state_code_xpath[0].text or False
    #     zip_xpath = address_node.xpath('cbc:PostalZone', namespaces=ns)
    #     zip = zip_xpath and zip_xpath[0].text and \
    #           zip_xpath[0].text.replace(' ', '') or False
    #     address_dict = {
    #         'zip': zip,
    #         'state_code': state_code,
    #         'country_code': country_code,
    #     }
    #     return address_dict

    # @api.model
    # def ubl_parse_delivery(self, delivery_node, ns):
    #     party_xpath = delivery_node.xpath('cac:DeliveryParty', namespaces=ns)
    #     if party_xpath:
    #         partner_dict = self.ubl_parse_party(party_xpath[0], ns)
    #     else:
    #         partner_dict = {}
    #     delivery_address_xpath = delivery_node.xpath(
    #         'cac:DeliveryLocation/cac:Address', namespaces=ns)
    #     if not delivery_address_xpath:
    #         delivery_address_xpath = delivery_node.xpath(
    #             'cac:DeliveryAddress', namespaces=ns)
    #     if delivery_address_xpath:
    #         address_dict = self.ubl_parse_address(
    #             delivery_address_xpath[0], ns)
    #     else:
    #         address_dict = {}
    #     delivery_dict = {
    #         'partner': partner_dict,
    #         'address': address_dict,
    #     }
    #     return delivery_dict
    #
    # def ubl_parse_incoterm(self, delivery_term_node, ns):
    #     incoterm_xpath = delivery_term_node.xpath("cbc:ID", namespaces=ns)
    #     if incoterm_xpath:
    #         incoterm_dict = {'code': incoterm_xpath[0].text}
    #         return incoterm_dict
    #     return {}
    #
    # def ubl_parse_product(self, line_node, ns):
    #     barcode_xpath = line_node.xpath(
    #         "cac:Item/cac:StandardItemIdentification/cbc:ID[@schemeID='GTIN']",
    #         namespaces=ns)
    #     code_xpath = line_node.xpath(
    #         "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns)
    #     product_dict = {
    #         'barcode': barcode_xpath and barcode_xpath[0].text or False,
    #         'code': code_xpath and code_xpath[0].text or False,
    #     }
    #     return product_dict
    #
    # # ======================= METHODS only needed for testing
    #
    # # Method copy-pasted from edi/base_business_document_import/
    # # models/business_document_import.py
    # # Because we don't depend on this module
    # def get_xml_files_from_pdf(self, pdf_file):
    #     """Returns a dict with key = filename, value = XML file obj"""
    #     logger.info('Trying to find an embedded XML file inside PDF')
    #     res = {}
    #     try:
    #         fd = BytesIO(pdf_file)
    #         pdf = PdfFileReader(fd)
    #         logger.debug('pdf.trailer=%s', pdf.trailer)
    #         pdf_root = pdf.trailer['/Root']
    #         logger.debug('pdf_root=%s', pdf_root)
    #         embeddedfiles = pdf_root['/Names']['/EmbeddedFiles']['/Names']
    #         i = 0
    #         xmlfiles = {}  # key = filename, value = PDF obj
    #         for embeddedfile in embeddedfiles[:-1]:
    #             mime_res = mimetypes.guess_type(embeddedfile)
    #             if mime_res and mime_res[0] in ['application/xml', 'text/xml']:
    #                 xmlfiles[embeddedfile] = embeddedfiles[i + 1]
    #             i += 1
    #         logger.debug('xmlfiles=%s', xmlfiles)
    #         for filename, xml_file_dict_obj in xmlfiles.items():
    #             try:
    #                 xml_file_dict = xml_file_dict_obj.getObject()
    #                 logger.debug('xml_file_dict=%s', xml_file_dict)
    #                 xml_string = xml_file_dict['/EF']['/F'].getData()
    #                 xml_root = etree.fromstring(xml_string)
    #                 logger.debug(
    #                     'A valid XML file %s has been found in the PDF file',
    #                     filename)
    #                 res[filename] = xml_root
    #             except Exception as e:
    #                 continue
    #     except Exception as e:
    #         pass
    #     logger.info('Valid XML files found in PDF: %s', list(res.keys()))
    #     return res
