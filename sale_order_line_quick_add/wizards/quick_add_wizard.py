# -*- coding: utf-8 -*-

from odoo import models, fields, api


class QuickOrderWizard(models.TransientModel):
    _name = "quick.order.wizard"

    name = fields.Char(string="Product Name")
    description = fields.Char()
    default_code = fields.Char("Internal Reference")
    category_id = fields.Many2one("product.category")
    line_ids = fields.One2many("quick.order.line.wizard", "wizard_id")
    order_id = fields.Many2one("sale.order")
    add_line_ids = fields.One2many("line.to.add", "quick_wizard_id")
    created = fields.Boolean()

    def action_add_lines(self):
        if self.add_line_ids:
            lines = []
            for line in self.add_line_ids:
                lines.append((0, 0, {
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.qty,
                    "product_uom": line.product_uom.id,
                }))
            self.order_id.order_line = lines

    @api.onchange("name", "description", "default_code", "category_id")
    def onchange_filter_fields(self):
        # print("add_line_ids", self.add_line_ids, self._origin.add_line_ids)
        domains = []
        if self.name and len(self.name) > 2:
            domains.append(("name", "ilike", self.name))
        if self.description and len(self.description) > 2:
            domains.append(("description_sale", "ilike", self.description))
        if self.category_id:
            domains.append(("categ_id", "child_of", self.category_id.id))
        if self.default_code and len(self.default_code) > 2:
            domains.append(("default_code", "ilike", self.default_code))
        # print("domains", domains)
        if domains:
            product_ids = self.env["product.product"].search(domains)
            self.line_ids = False
            if product_ids:
                new_lines = []
                for product_id in product_ids:
                    product_line = self._origin.add_line_ids.filtered(lambda l: l.product_id.id == product_id.id)
                    qty = 0
                    product_uom = product_id.uom_id.id
                    if product_line:
                        print("product_line.product_uom--------->", product_line.product_uom.name)
                        qty = product_line.qty
                        product_uom = product_line.product_uom.id
                    new_lines.append((0, 0, {
                        "product_id": product_id.id,
                        "qty": qty,
                        "product_uom": product_uom,
                    }))
                self.line_ids = new_lines


class QuickOrderWizardLine(models.TransientModel):
    _name = "quick.order.line.wizard"

    product_id = fields.Many2one("product.product")
    description = fields.Text(related="product_id.description_sale")
    default_code = fields.Char(related="product_id.default_code")
    category_id = fields.Many2one("product.category", related="product_id.categ_id")
    product_template_variant_value_ids = fields.Many2many(related="product_id.product_template_variant_value_ids")
    lst_price = fields.Float(related="product_id.lst_price")
    standard_price = fields.Float(related="product_id.standard_price")
    type = fields.Selection(related="product_id.type")
    qty_available = fields.Float(related="product_id.qty_available")
    virtual_available = fields.Float(related="product_id.virtual_available")
    uom_id = fields.Many2one(related="product_id.uom_id")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    wizard_id = fields.Many2one("quick.order.wizard")
    qty = fields.Float()
    product_uom = fields.Many2one("uom.uom", domain="[('category_id', '=', product_uom_category_id)]")

    @api.onchange("qty", "product_uom")
    def onchange_qty(self):
        print("self.product_uom.id", self.product_uom.name)
        added_product_line_id = self.wizard_id._origin.add_line_ids.filtered(
            lambda line: line.product_id.id == self.product_id.id)
        if added_product_line_id:
            added_product_line_id.qty = self.qty
            added_product_line_id.product_uom = self.product_uom.id
        else:
            self.wizard_id._origin.add_line_ids = [
                (0, 0, {"product_id": self.product_id.id, "qty": self.qty, "product_uom": self.product_uom.id})]


class LinesToAdd(models.TransientModel):
    _name = "line.to.add"

    product_id = fields.Many2one("product.product")
    qty = fields.Float()
    product_uom = fields.Many2one("uom.uom")
    quick_wizard_id = fields.Many2one("quick.order.wizard")
