# -*- coding: utf-8 -*-

from odoo import api, models


class ProductPricelistReport(models.AbstractModel):
    _name = 'report.product_pricelist_matrix.report_pricelist'
    _description = 'Pricelist Report Matrix'

    def _get_report_values(self, docids, data):
        return self._get_report_data(data, 'pdf')

    @api.model
    def get_html(self, data):
        render_values = self._get_report_data(data, 'html')
        return self.env.ref('product_pricelist_matrix.report_pricelist_page')._render(render_values)

    def _get_report_data(self, data, report_type='html'):
        # print("data", data)
        domain = [("active", "=", True)]
        if data.get("pricelist_ids"):
            domain.append(("id", "in", data.get("pricelist_ids")))
            pricelist_ids = self.env['product.pricelist'].search(domain)
        else:
            pricelist_ids = self.env['product.pricelist'].search(domain, limit=1)
        active_model = data['active_model']
        active_ids = data.get('active_ids') or []
        is_product_tmpl = active_model == 'product.template'
        ProductClass = self.env[active_model]

        products = ProductClass.browse(active_ids) if active_ids else ProductClass.search([('sale_ok', '=', True)])
        products_data = [
            self._get_product_data(is_product_tmpl, product, pricelist_ids)
            for product in products
        ]

        return {
            'is_html_type': report_type == 'html',
            'is_product_tmpl': is_product_tmpl,
            'is_visible_title': bool(data['is_visible_title']) or False,
            'pricelist_ids': pricelist_ids,
            'products': products_data,
            'show_cost': data.get("show_cost"),
            'show_qty_on_hand': data.get("show_qty_on_hand"),
        }

    def _get_product_data(self, is_product_tmpl, product, pricelist_ids):
        data = {
            'id': product.id,
            'code': product.default_code,
            'name': product.name,
            'price': dict.fromkeys(pricelist_ids, 0.0),
            'uom': product.uom_id.name,
            'cost_price': product.standard_price,
            'qty_available': product.qty_available,
        }
        for pricelist_id in pricelist_ids:
            data['price'][pricelist_id] = pricelist_id.get_product_price(product, 1, False)

        if is_product_tmpl and product.product_variant_count > 1:
            data['variants'] = [
                self._get_product_data(False, variant, pricelist_ids)
                for variant in product.product_variant_ids
            ]

        return data
