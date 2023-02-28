# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

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
                            'product_name': lot.product_id.name,
                            'quantity': line.qty if lot.product_id.tracking == 'lot' else 1.0,
                            'uom_name': line.product_uom_id.name,
                            'lot_name': lot.lot_name,
                            'expiry_date': lot_id.expiration_date.strftime('%d/%m/%Y') if lot_id and lot_id.expiration_date else False, 
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
                    'product_name': lot.product_id.display_name,
                    'quantity': formatLang(self.env, invoiced_lot_qty, dp='Product Unit of Measure'),
                    'uom_name': lot.product_uom_id.name,
                    'lot_name': lot.name,
                    'lot_id': lot.id,
                    'expiry_date': lot.expiration_date.strftime('%d/%m/%Y') if lot.expiration_date else False
                })
        return res