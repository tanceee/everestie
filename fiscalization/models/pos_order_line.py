from odoo import api, fields, models, _


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    # INVOICE ITEMS

    invoice_item_name = fields.Char(related='product_id.name', size=50)
    invoice_item_code = fields.Char(related='product_id.barcode', size=50)
    invoice_item_unit_of_measure = fields.Char(related='product_id.uom_id.name', size=50)
    invoice_item_quantity = fields.Float(digits=(12, 3)) # qty
    invoice_item_unit_price_before_vat = fields.Float(digits=(12, 2))  # price_subtotal/qty
    invoice_item_unit_price_after_vat = fields.Float(digits=(12, 2))  # price_unit
    invoice_item_rebate = fields.Float(digits=(12, 2))  # discount
    does_item_rebate_reduce_base_price = fields.Boolean("A e ul zbritja shumen e bazes tatimore?")
    invoice_item_vat_rate = fields.Float(digits=(12, 2))  # tax_ids_after_fiscal_position
    invoice_item_type_of_exempt_from_vat = fields.Selection(selection=[('type_1', 'TYPE_1'),
                                                                       ('type_2', 'TYPE_2'),
                                                                       ('tax_free', 'TAX_FREE'),
                                                                       ('margin_scheme', 'MARGIN_SCHEME'),
                                                                       ('export_of_goods', 'EXPORT_OF_GOODS')],
                                                            default='type_1')  # not applicable for the moment
    invoice_item_vat_amount = fields.Float(digits=(12, 2))  # price_subtotal_incl-price_subtotal
    invoice_item_is_investment = fields.Boolean("A jane artikujt e blere investim?")
    invoice_item_price_after_vat_apply = fields.Float(digits=(12, 2))  # price_subtotal_incl
