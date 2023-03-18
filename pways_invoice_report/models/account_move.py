# -*- coding: utf-8 -*-
try:
   import qrcode
except ImportError:
   qrcode = None
try:
   import base64
except ImportError:
   base64 = None

from io import BytesIO


from datetime import datetime
import pytz

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict
from odoo.exceptions import UserError

from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = "account.move"

    total_tax_subtotal = fields.Monetary(string='Total Amount with Tax', compute='_compute_tax_subtotal', help="Total tax subtotal for the invoice")
    total_no_tax_subtotal = fields.Monetary(string='Total Amount with NO Tax', compute='_compute_tax_subtotal', help="Total NO tax subtotal for the invoice")
    license_plate_no = fields.Char(string="License Plate No")
    serial_number = fields.Char(string="Serial No")
    delivery_time = fields.Char(string="Delivery Time")
    transportuesi = fields.Many2one('res.partner', string="Transportuesi")
    qr_code_payment = fields.Binary('QRcode', compute="_generate_qr")
    qr_code_product_details = fields.Binary('Product Barcode', compute="_generate_qr_product")

    def _generate_qr(self):
       for rec in self:
           if qrcode and base64:
              
               qr = qrcode.QRCode(
                   version=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                   box_size=3,
                   border=4,
               )
               qr.add_data("Payment Reference : ")
               qr.add_data(rec.payment_reference)
               qr.add_data("\n")
               qr.add_data("Custome Name : ")
               qr.add_data(rec.partner_id.name)
               qr.add_data("\n")
               qr.add_data("journal: ")
               qr.add_data(rec.journal_id.name)
               qr.add_data("Bank: ")
               qr.add_data(rec.journal_id.name)
               qr.add_data("\n")
               qr.add_data("Total Amount: ")
               qr.add_data(rec.amount_total)
               qr.make(fit=True)
               img = qr.make_image()
               temp = BytesIO()
               img.save(temp, format="PNG")
               qr_image = base64.b64encode(temp.getvalue())
               rec.update({'qr_code_payment':qr_image})
           else:
               raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

    def _generate_qr_product(self):
        for rec in self:
           if qrcode and base64:
                qr = qrcode.QRCode(
                   version=1,
                   error_correction=qrcode.constants.ERROR_CORRECT_L,
                   box_size=3,
                   border=4,
                )
                qr.add_data("Custome Name : ")
                qr.add_data(rec.partner_id.name)
                qr.add_data("\n")
                qr.add_data("Product Details : ")
                qr.add_data("\n")
                for line in rec.invoice_line_ids:
                    qr.add_data("Name : ")
                    qr.add_data(line.product_id.name)
                    qr.add_data(", ")
                    qr.add_data("UOM : ")
                    qr.add_data(line.product_uom_id.name)
                    qr.add_data(", ")
                    qr.add_data("Qty : ")
                    qr.add_data(line.quantity)
                    qr.add_data(", ")
                    qr.add_data("Price : ")
                    qr.add_data(line.price_unit)
                    qr.add_data(", ")
                    qr.add_data("Sub Total : ")
                    qr.add_data(line.price_subtotal)
                    qr.add_data(", ")
                    qr.add_data("\n")
                qr.add_data("Total Amount: ")
                qr.add_data(rec.amount_total)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code_product_details':qr_image})
           else:
               raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))
    
    def _compute_tax_subtotal(self):
        self.total_tax_subtotal = sum(line.tax_subtotal for line in self.invoice_line_ids)
        self.total_no_tax_subtotal= self.amount_untaxed - self.total_tax_subtotal

    @api.onchange('transportuesi')
    def _onchange_transportuesi_id(self):
        if self.transportuesi and self.transportuesi.license_plate_no:
            self.license_plate_no = self.transportuesi.license_plate_no

    @api.onchange('user_id', 'company_id','partner_id')
    def _onchange_partner_id(self):
        super(AccountMove, self)._onchange_partner_id()
        # if self.user_id and self.user_id.license_plate_no:
        #     self.license_plate_no = self.user_id.license_plate_no
        if self.user_id and not self.transportuesi:
                self.transportuesi = self.env['res.users'].search([('partner_id.name', 'ilike', self.user_id.name)]).mapped('partner_id')

    def convert_TZ_UTC(self, TZ_datetime):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        if local:
            time = datetime.strftime(pytz.utc.localize(datetime.strptime(TZ_datetime, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %H:%M:%S")
            return time

    def _get_invoiced_lot_values(self):
        """ Get and prepare data to show a table of invoiced lot on the invoice's report. """
        self.ensure_one()

        res = super(AccountMove, self)._get_invoiced_lot_values()
        res =[]
        if self.state == 'draft' or not self.invoice_date or self.move_type not in ('out_invoice', 'out_refund'):
            return res

        current_invoice_amls = self.invoice_line_ids.filtered(lambda aml: not aml.display_type and aml.product_id and aml.quantity)
        all_invoices_amls = current_invoice_amls.sale_line_ids.invoice_lines.filtered(lambda aml: aml.move_id.state == 'posted').sorted(lambda aml: (aml.date, aml.move_name, aml.id))
        index = all_invoices_amls.ids.index(current_invoice_amls[:1].id) if current_invoice_amls[:1] in all_invoices_amls else 0
        previous_amls = all_invoices_amls[:index]

        previous_qties_invoiced = previous_amls._get_invoiced_qty_per_product()
        invoiced_qties = current_invoice_amls._get_invoiced_qty_per_product()
        invoiced_products = invoiced_qties.keys()

        qties_per_lot = defaultdict(float)
        previous_qties_delivered = defaultdict(float)
        stock_move_lines = current_invoice_amls.sale_line_ids.move_ids.move_line_ids.filtered(lambda sml: sml.state == 'done' and sml.lot_id).sorted(lambda sml: (sml.date, sml.id))
        for sml in stock_move_lines:
            if sml.product_id not in invoiced_products or 'customer' not in {sml.location_id.usage, sml.location_dest_id.usage}:
                continue
            product = sml.product_id
            product_uom = product.uom_id
            qty_done = sml.product_uom_id._compute_quantity(sml.qty_done, product_uom)

            if sml.location_id.usage == 'customer':
                returned_qty = min(qties_per_lot[sml.lot_id], qty_done)
                qties_per_lot[sml.lot_id] -= returned_qty
                qty_done = returned_qty - qty_done

            previous_qty_invoiced = previous_qties_invoiced[product]
            previous_qty_delivered = previous_qties_delivered[product]
            # If we return more than currently delivered (i.e., qty_done < 0), we remove the surplus
            # from the previously delivered (and qty_done becomes zero). If it's a delivery, we first
            # try to reach the previous_qty_invoiced
            if float_compare(qty_done, 0, precision_rounding=product_uom.rounding) < 0 or \
                    float_compare(previous_qty_delivered, previous_qty_invoiced, precision_rounding=product_uom.rounding) < 0:
                previously_done = qty_done if sml.location_id.usage == 'customer' else min(previous_qty_invoiced - previous_qty_delivered, qty_done)
                previous_qties_delivered[product] += previously_done
                qty_done -= previously_done

            qties_per_lot[sml.lot_id] += qty_done

        if self.sudo().pos_order_ids:
            for order in self.sudo().pos_order_ids:
                for line in order.lines:
                    lots = line.pack_lot_ids
                    for lot in lots:
                        lot_id = self.env['stock.production.lot'].search([('name', '=', lot.lot_name),('product_id', '=', lot.product_id.id)], limit=1)
                        res.append({
                            'product_id': lot.product_id.id,
                            'product_name': lot.product_id.name,
                            'quantity': line.qty if lot.product_id.tracking == 'lot' else 1.0,
                            'uom_name': line.product_uom_id.name,
                            'lot_name': lot.lot_name,
                            'expiry_date': self.convert_TZ_UTC(fields.Datetime.to_string(lot_id.expiration_date)) if lot_id and lot_id.expiration_date else False, 
                        })
        else:
            for lot, qty in qties_per_lot.items():
                # access the lot as a superuser in order to avoid an error
                # when a user prints an invoice without having the stock access
                lot = lot.sudo()
                if float_is_zero(invoiced_qties[lot.product_id], precision_rounding=lot.product_uom_id.rounding) \
                        or float_compare(qty, 0, precision_rounding=lot.product_uom_id.rounding) <= 0:
                    continue
                invoiced_lot_qty = min(qty, invoiced_qties[lot.product_id])
                invoiced_qties[lot.product_id] -= invoiced_lot_qty
                res.append({
                    'product_id': lot.product_id.id,
                    'product_name': lot.product_id.display_name,
                    'quantity': formatLang(self.env, invoiced_lot_qty, dp='Product Unit of Measure'),
                    'uom_name': lot.product_uom_id.name,
                    'lot_name': lot.name,
                    'lot_id': lot.id,
                    'expiry_date': self.convert_TZ_UTC(fields.Datetime.to_string(lot_id.expiration_date)) if lot.expiration_date else False
                })
        return res

class LineInherit(models.AbstractModel):
    _inherit = 'account.move.line'
    
    tax_subtotal = fields.Monetary(string='Amount with Tax', compute='_compute_only_taxes', help="Tax Subtotal for each line")

    @api.depends('tax_ids', 'price_subtotal', 'tax_subtotal')
    def _compute_only_taxes(self):
        if self.tax_ids and not self.tax_ids[0].amount == 0:
            self.tax_subtotal = self.price_subtotal

class JournalInherit(models.AbstractModel):
    _inherit = 'account.journal'

    display_bank = fields.Boolean(string='Display Bank', copy=False)
