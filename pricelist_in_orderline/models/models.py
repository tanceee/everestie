# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_pricelist_id = fields.Many2one('product.pricelist')
    price_details_html = fields.Html()

    @api.onchange("product_id", "product_uom_qty", "product_uom")
    def set_price_detail(self):
        if self.product_id and self.product_uom_qty and self.product_uom and self.order_id.partner_id:
            pricelist_with_price = []
            pricelist_ids = self.env["product.pricelist"].search([('currency_id', '=', self.currency_id.id)])
            products_qty_partner = [(self.product_id.id, self.product_uom_qty, self.order_id.partner_id.id)]
            categ_ids = {}
            for p in self.product_id:
                categ = p.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
            categ_ids = list(categ_ids)
            for pricelist_id in pricelist_ids:
                items = pricelist_id._compute_price_rule_get_items(products_qty_partner, fields.Datetime.now(),
                                                                   self.product_uom.id,
                                                                   self.product_id.product_tmpl_id.ids,
                                                                   self.product_id.ids,
                                                                   categ_ids)
                if not items:
                    continue

                monetary_options = {'display_currency': self.currency_id}

                price = pricelist_id.get_product_price(self.product_id, self.product_uom_qty,
                                                       self.order_id.partner_id,
                                                       uom_id=self.product_uom.id)
                price_html = self.env['ir.qweb.field.monetary'].value_to_html(price, monetary_options)
                pricelist_with_price.append([pricelist_id.name, price_html])
            self.price_details_html = self.env['ir.ui.view']._render_template(
                "pricelist_in_orderline.pricelist_price_info", {'pricelist_with_price': pricelist_with_price})
        else:
            self.price_details_html = "<em>Required fields not set to get the pricelist price</em>"

    @api.onchange("product_id")
    def set_line_pricelist(self):
        if self.product_id:
            self.line_pricelist_id = self.order_id.pricelist_id.id
        else:
            self.line_pricelist_id = False

    @api.onchange("line_pricelist_id")
    def set_pricelist_price(self):
        if self.line_pricelist_id and self.product_id and self.product_uom_qty and self.product_uom:
            price = self.line_pricelist_id.get_product_price(self.product_id, self.product_uom_qty,
                                                             self.order_id.partner_id,
                                                             uom_id=self.product_uom.id)
            self.price_unit = price
        else:
            self.price_unit = 0
