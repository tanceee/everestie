# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from io import BytesIO

import requests
from dateutil.tz import tz
from lxml import etree
from odoo.addons.fiscalization_base.services.http_calls.request import make_http_call

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..service import wtnic
from ..service.warehouse_transfer_note import make_wtn

import qrcode
import logging

logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_internal_picking = fields.Boolean()
    transfer_user_id = fields.Many2one("res.users", default=lambda self: self.env.user)

    wtn_type = fields.Selection(
        [('WTN', '[WTN] WTN without changing ownership'),
         ('SALE', '[SALE] Transport document for sale of fuels.')])
    wtn_transaction = fields.Selection(
        [('SALES', '[SALES] Regular sales transaction type for fuels.'),
         ('EXAMINATION', '[EXAMINATION] Examination transaction type for fuels.'),
         ('TRANSFER', '[TRANSFER] Transfer transaction type.'),
         ('DOOR', '[DOOR] The goods are transferred for door to door sales transaction type.')], default='TRANSFER')
    subsequent_delivery_type = fields.Selection([
        ('NOINTERNET', '[NOINTERNET] When TCR operates in the area where there is no Internet available.'),
        ('BOUNDBOOK', '[BOUNDBOOK] When TCR is not working and message cannot be created with TCR.'),
        ('SERVICE', '[SERVICE] When there is an issue with the fiscalization service that blocks fiscalization.'),
        ('TECHNICALERROR',
         '[TECHNICALERROR] When there is a temporary technical error at TCR side that prevents successful fiscalization.')])

    issue_date_time = fields.Datetime(help="Date and time of creation of the WTN.", copy=False)

    wtn_ordinal_number = fields.Char(copy=False)
    wth_number = fields.Char(copy=False)  # wtn_ordinal_number/Year

    value_of_goods = fields.Float(help="Cost of goods at cost price.")
    veh_ownership = fields.Selection([("OWNER", "[OWNER] Issuer is owner of the vehicle."),
                                      ("THIRDPARTY", "[THIRDPARTY] Third party is owner of the vehicle.")])
    veh_plates = fields.Char(help="Plates of the vehicle that will transport the goods.", size=30)

    # Source Address Details
    start_address = fields.Text(help="Address of the starting point of transportation.", size=400)
    start_city = fields.Char(help="City of the starting point of transportation.", size=200)
    start_date_time = fields.Datetime(help="Date and time of the transport departure from start address.", copy=False)
    start_point = fields.Selection([('WAREHOUSE', '[WAREHOUSE] Warehouse'),
                                    ('EXHIBITION', '[EXHIBITION] Exhibition'),
                                    ('STORE', '[STORE] Store'),
                                    ('SALE', '[SALE] Point of sale'),
                                    ('ANOTHER', '[ANOTHER] Another person\'s warehouse'),
                                    ('CUSTOMS', '[CUSTOMS] Customs warehouse'),
                                    ('OTHER', '[OTHER] Other')], default='WAREHOUSE', help="Type of start point.")

    # Destination Address Details
    des_address = fields.Text(help="Address of destination.", size=400)
    des_city = fields.Char(help="City of destination.", size=200)
    des_date_time = fields.Datetime(help="Expected date when the goods should arrive to its destination.", copy=False)
    des_point = fields.Selection([('WAREHOUSE', '[WAREHOUSE] Warehouse'),
                                  ('EXHIBITION', '[EXHIBITION] Exhibition'),
                                  ('STORE', '[STORE] Store'),
                                  ('SALE', '[SALE] Point of sale'),
                                  ('OTHER', '[OTHER] Other')], default='WAREHOUSE', help="Type of destination point.")

    is_goods_flammable = fields.Boolean(help="Are goods flammable or not.")
    is_escort_required = fields.Boolean(help="Is escort required or not.")

    pack_type = fields.Char(size=50, help="Type of packaging.")
    pack_num = fields.Integer(help="Number of packs.")
    items_num = fields.Integer(help="Number of items of goods.")

    wtnic = fields.Char(help="Warehouse transfer note identification code.", size=32, copy=False)
    wtnic_signature = fields.Text(help="Signed warehouse transfer note identification code concatenated parameters.",
                                  size=512, copy=False)

    issuer_nuis = fields.Char(help="NUIS of the WTN issuer.", size=10)
    issuer_name = fields.Char(help="Name of the WTN issuer.", size=200)
    issuer_address = fields.Text(help="Address of the WTN issuer.", size=400)
    issuer_town = fields.Char(help="Town of the WTN issuer.", size=200)

    carrier_id = fields.Many2one("res.partner")
    carrier_id_type = fields.Selection([('NUIS', '[NUIS] NUIS number'), ('ID', '[ID] Personal ID number')],
                                       help="Carrier's identification number type.")
    carrier_id_num = fields.Char(help="Carrier's identification number.", size=20)
    carrier_name = fields.Char(help="Carrier's name.", size=200)
    carrier_address = fields.Text(help="Carrier's address.", size=400)
    carrier_town = fields.Char(help="Carrier's town.", size=200)

    fwtnic = fields.Char(copy=False)
    is_fiscalized = fields.Boolean(copy=False)

    @api.onchange("carrier_id")
    def set_carrier_details(self):
        if self.carrier_id:
            if self.carrier_id.vat_type in ["NUIS", "ID"]:
                self.carrier_id_type = self.carrier_id.vat_type
                self.carrier_id_num = self.carrier_id.vat
                self.carrier_name = self.carrier_id.display_name
                self.carrier_address = self.carrier_id._display_address()
                self.carrier_town = self.carrier_id.city
            else:
                raise ValidationError('Selected carrier "VAT Type" must be in ["NUIS", "ID"], Update the carrier.')
        else:
            self.carrier_id_type = False
            self.carrier_id_num = False
            self.carrier_name = False
            self.carrier_address = False
            self.carrier_town = False

    @api.model
    def create(self, vals):
        rec = super(StockPicking, self).create(vals)
        if rec.picking_type_id.code == "internal":
            seq_id = rec.picking_type_id.sequence_id
            next_seq_number = seq_id.get_next_without_consume()
            if not next_seq_number:
                raise ValidationError("There is some issue with the transfer note sequence number. Contact Admin!")
            transfer_seq_number = next_seq_number - 1
            # number = self.env['ir.sequence'].next_by_code('warehouse.transfer.note.sequence.number')
            rec.wtn_ordinal_number = transfer_seq_number
            rec.wth_number = str(transfer_seq_number) + '/' + str(
                datetime.now().astimezone().replace(microsecond=0).year)
            rec.issuer_nuis = rec.company_id.vat
            rec.issuer_name = rec.company_id.name
            address_data = rec.company_id.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = rec.company_id.partner_id.browse(address_data['contact']).sudo()
                rec.issuer_address = partner._display_address()
            rec.issuer_town = rec.company_id.partner_id.city

            rec._onchange_picking_type()
            # rec._onchange_partner_id()
        return rec

    @api.onchange("picking_type_id")
    def check_picking_type(self):
        if self.picking_type_id:
            if self.picking_type_id.code == 'internal':
                self.is_internal_picking = True
            else:
                self.is_internal_picking = False
        else:
            self.is_internal_picking = False

    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        if self.move_ids_without_package:
            total_line_items_cost = 0
            total_item_nums = 0
            for move_id in self.move_ids_without_package:
                standard_price = move_id.product_id.standard_price
                quantity_done = move_id.quantity_done
                total_line_items_cost += standard_price * quantity_done
                total_item_nums += quantity_done
                # print("QTy", quantity_done)
            self.value_of_goods = total_line_items_cost
            # print("total", total_item_nums)
            self.items_num = total_item_nums
        self.start_date_time = self.date_done

        return result

    @api.onchange('picking_type_id', 'location_id', 'location_dest_id')
    def _onchange_picking_type_custom(self):
        if self.picking_type_id:
            if self.picking_type_id.code == 'internal':
                self.wtn_type = 'WTN'
            # else:
            #     self.wtn_type = 'SALE'
            # if self.picking_type_id.warehouse_id:
            #     partner_id = self.picking_type_id.warehouse_id.partner_id
            #     self.start_address = partner_id._display_address()
            #     self.start_city = partner_id.city
        else:
            self.wtn_type = False

        if self.location_id and self.wtn_type == 'WTN':
            source_warehouse_id = self.location_id.warehouse_id
            if not source_warehouse_id:
                raise ValidationError("Source Warehouse is not configured!!!")
            partner_id = source_warehouse_id.partner_id
            self.start_address = partner_id._display_address()
            self.start_city = partner_id.city
            self.start_point = source_warehouse_id.warehouse_type
        else:
            self.start_address = False
            self.start_city = False
            self.start_point = False

        if self.location_dest_id and self.wtn_type == 'WTN':
            source_warehouse_id = self.location_dest_id.warehouse_id
            if not source_warehouse_id:
                raise ValidationError("Source Warehouse is not configured!!!")
            partner_id = source_warehouse_id.partner_id
            self.des_address = partner_id._display_address()
            self.des_city = partner_id.city
            self.des_point = source_warehouse_id.warehouse_type

        else:
            self.des_address = False
            self.des_city = False
            self.des_point = False

    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     if self.partner_id:
    #         self.des_address = self.partner_id._display_address()
    #         self.des_city = self.partner_id.city

    @api.onchange('subsequent_delivery_type')
    def onchange_subsequent_delivery_type(self):
        if self.subsequent_delivery_type:
            self.issue_date_time = self.date_done
        else:
            self.issue_date_time = self.date_done

    @api.onchange('veh_ownership')
    def onchange_veh_ownership(self):
        if self.veh_ownership == 'OWNER':
            self.carrier_id_type = False
            self.carrier_id_num = False
            self.carrier_name = False
            self.carrier_address = False
            self.carrier_town = False

    def register_wtn(self):
        if self.move_ids_without_package:
            total_line_items_cost = 0
            total_item_nums = 0
            for move_id in self.move_ids_without_package:
                standard_price = move_id.product_id.standard_price
                quantity_done = move_id.quantity_done
                total_line_items_cost += standard_price * quantity_done
                total_item_nums += quantity_done
            self.value_of_goods = total_line_items_cost
            self.items_num = total_item_nums

        self.start_date_time = self.date_done
        if not self.issue_date_time:
            self.issue_date_time = self.date_done
        vals_dict = {field: getattr(self, field, None) for field in dir(self)}
        busin_unit_code = self.operating_unit_id.business_unit_code
        soft_code = self.company_id.software_code
        operator_code = self.transfer_user_id.operator_code
        if not operator_code:
            raise ValidationError(
                "User without an Operator Code can't register WTN! Please contact your administrator.")

        temp_dict = {
            "busin_unit_code": busin_unit_code,
            "soft_code": soft_code,
            "operator_code": operator_code
        }
        vals_dict.update(temp_dict)

        company_id = self.env.user.company_id

        company_p12_certificate = company_id.p12_certificate
        company_p12_certificate = base64.b64decode(company_p12_certificate)
        certificate_password = company_id.certificate_password.encode('utf-8')
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Tirane')
        if self.issue_date_time:
            issue_date_time = self.issue_date_time.replace(
                tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
                microsecond=0).isoformat()
        else:
            issue_date_time = self.date_done.replace(
                tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
                microsecond=0).isoformat()
        if not self.issuer_nuis:
            raise ValidationError("Issuer Tax ID Missing!")

        if not issue_date_time:
            raise ValidationError("Issue Datetime Missing!")

        if not self.wth_number:
            raise ValidationError("Warehouse Transfer Note Number Missing!")

        if not busin_unit_code:
            raise ValidationError("Business Unit Code Missing!")

        if not soft_code:
            raise ValidationError("Software Code Missing!")

        wtnic_input = wtnic.build_wtnic_input(self.issuer_nuis, issue_date_time, self.wth_number, busin_unit_code,
                                              soft_code)
        self.wtnic = vals_dict['wtnic'] = wtnic.generate_wtnic(wtnic_input=wtnic_input,
                                                               company_p12_certificate=company_p12_certificate,
                                                               certificate_password=certificate_password)
        self.wtnic_signature = vals_dict['wtnic_signature'] = wtnic.generate_wtnic_signature(wtnic_input=wtnic_input,
                                                                                             company_p12_certificate=company_p12_certificate,
                                                                                             certificate_password=certificate_password)

        vals_dict.update(temp_dict)

        final_xml = make_wtn(vals_dict, company_p12_certificate=company_p12_certificate,
                             certificate_password=certificate_password)
        print("XML", final_xml)

        try:
            url = company_id.fiscalization_endpoint
            response = make_http_call(final_xml, url)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise ValidationError(e)
            #
        if response:
            print("Response", str(response))
            fwtnic = None
            root = etree.fromstring(response)
            for element in root.iter('{https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema}FWTNIC'):
                fwtnic = element.text
            if fwtnic:
                self['fwtnic'] = fwtnic
                self['is_fiscalized'] = True

            else:
                self['is_fiscalized'] = False
                for faultcode in root.iter('faultcode'):
                    for faultstring in root.iter('faultstring'):
                        raise ValidationError("Fault Code: %s \n Fault String: %s" % (faultcode.text, faultstring.text))

    def make_wtn_qr_code(self):
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=10, border=4)
        company_id = self.env.user.company_id
        url = company_id.wtn_check_endpoint
        wtnic = self.wtnic
        issuer_nuis = self.issuer_nuis
        issue_date_time = self.issue_date_time
        wtn_ordinal_number = self.wtn_ordinal_number
        business_unit_code = self.operating_unit_id.business_unit_code
        soft_code = self.company_id.software_code
        from_zone = tz.gettz('UTC')
        if not issue_date_time:
            issue_date_time = self.date_done.replace(
                tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
                microsecond=0).isoformat()
        else:
            issue_date_time = self.issue_date_time.replace(
                tzinfo=from_zone).astimezone(tz.gettz('Europe/Tirane')).replace(
                microsecond=0).isoformat()

        if all([url, wtnic, issuer_nuis, issue_date_time, wtn_ordinal_number, business_unit_code, soft_code]):
            qr.add_data(
                url +
                "?wtnic=" + wtnic +
                "&tin=" + issuer_nuis +
                "&crtd=" + str(issue_date_time) +
                "&ord=" + wtn_ordinal_number +
                "&bu=" + business_unit_code +
                "&sw=" + soft_code
            )
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            return qr_image
        else:
            raise ValidationError(
                "Some required field values are missing! Failed to add the WTN QR Code. Fields required for WTN QR Code"
                "\nAPI Endpoint, wtnic, issuer nuis, issue datetime,business unit code,software code")


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    warehouse_type = fields.Selection([('WAREHOUSE', '[WAREHOUSE] Warehouse'),
                                       ('EXHIBITION', '[EXHIBITION] Exhibition'),
                                       ('STORE', '[STORE] Store'),
                                       ('SALE', '[SALE] Point of sale'),
                                       ('ANOTHER', '[ANOTHER] Another person\'s warehouse'),
                                       ('CUSTOMS', '[CUSTOMS] Customs warehouse'),
                                       ('OTHER', '[OTHER] Other')], default='WAREHOUSE', help="Type of Warehouse.")

    # des_point = fields.Selection([('WAREHOUSE', '[WAREHOUSE] Warehouse'),
    #                               ('EXHIBITION', '[EXHIBITION] Exhibition'),
    #                               ('STORE', '[STORE] Store'),
    #                               ('SALE', '[SALE] Point of sale'),
    #                               ('OTHER', '[OTHER] Other')], default='WAREHOUSE', help="Type of destination point.")


class ResCompany(models.Model):
    _inherit = "res.company"

    wtn_check_endpoint = fields.Char()
