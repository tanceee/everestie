# -*- coding: utf-8 -*-
import base64
import io
import json
import logging

import xlsxwriter

from odoo import http, fields
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)


def format_currency_amount(amount, currency_id):
    fmt = "%.{0}f".format(currency_id.decimal_places)
    lang = request.env['ir.qweb.field'].user_lang()

    formatted_amount = lang.format(fmt, currency_id.round(amount),
                                   grouping=True, monetary=True).replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-',
                                                                                                              u'-\N{ZERO WIDTH NO-BREAK SPACE}')
    pre = currency_id.position == 'before'
    symbol = u'{symbol}'.format(symbol=currency_id.symbol or '')
    return u'{pre}{0}{post}'.format(formatted_amount, pre=symbol if pre else '', post=symbol if not pre else '')


class PricelistMatrix(http.Controller):

    @http.route('/product_pricelist_matrix/fetch_default_pricelist', type='json', auth='user')
    def fetch_default_pricelist(self):
        default_pricelist = request.env['product.pricelist'].search_read([], ['id', 'name', 'display_name'], limit=1)
        return {
            "default_pricelist": default_pricelist
        }

    @http.route('/product_pricelist_matrix/excel', type='http', auth='user', csrf=False, methods=['POST'])
    def get_pricelist_excel(self, **kwargs):
        data = json.loads(kwargs.get("data"))
        report_data = request.env["report.product_pricelist_matrix.report_pricelist"]._get_report_data(data,
                                                                                                       report_type="excel")

        report = self.render_excel_pricelist(report_data)
        file_content = base64.b64decode(report or "")

        filename = "Product Pricelist - " + fields.Datetime.now().strftime("%Y/%m/%d") + ".xlsx"

        content_type = ('Content-Type', 'application-/octet-stream')
        disposition_content = ('Content-Disposition', content_disposition(filename))
        return request.make_response(file_content, [content_type, disposition_content])

    def render_excel_pricelist(self, values_to_render):
        is_product_tmpl = values_to_render.get("is_product_tmpl")
        products = values_to_render.get("products")
        pricelist_ids = values_to_render.get("pricelist_ids")
        show_cost = values_to_render.get("show_cost")
        show_qty_on_hand = values_to_render.get("show_qty_on_hand")

        col_count = 3 + len(pricelist_ids)
        if show_cost:
            col_count += 1
        if show_qty_on_hand:
            col_count += 1
        target_stream = io.BytesIO()
        workbook = xlsxwriter.Workbook(target_stream)
        worksheet = workbook.add_worksheet("Product Pricelist")

        head_format = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'bold': True, 'bg_color': '#c0c0c0'})
        head_format_center = workbook.add_format(
            {'valign': 'vcenter', 'align': 'center', 'bold': True, 'bg_color': 'yellow'})
        head_format_left = workbook.add_format({'valign': 'vcenter', 'bold': True, })
        format_bold_left = workbook.add_format({'valign': 'vcenter', 'bold': True, 'align': 'left'})
        format_bold_right = workbook.add_format({'valign': 'vcenter', 'bold': True, 'align': 'right'})
        format_bold_center = workbook.add_format({'valign': 'vcenter', 'bold': True, 'align': 'center'})
        format_center = workbook.add_format({'valign': 'vcenter', 'bold': False, 'align': 'center'})
        format_right = workbook.add_format({'valign': 'vcenter', 'bold': False, 'align': 'right'})

        table_row = 4
        for i in range(col_count):
            worksheet.set_column(0, i, 20)
        if products:
            worksheet.merge_range(0, 0, 1, col_count - 1, "Product Pricelist", head_format_center)
            worksheet.write('A4', 'Internal Ref.', head_format)
            worksheet.write('B4', 'Products', head_format)
            worksheet.write('C4', 'UoM', head_format)
            char_val = 68
            if show_cost:
                worksheet.write('%s4' % chr(char_val), 'Cost Price', head_format)
                char_val += 1
            if show_qty_on_hand:
                worksheet.write('%s4' % chr(char_val), 'Qty. On-Hand', head_format)
                char_val += 1

            for pricelist_id in pricelist_ids:
                worksheet.write('%s4' % chr(char_val), pricelist_id.name, head_format)
                char_val += 1

            if is_product_tmpl:
                for pricelist_product in values_to_render.get("products"):
                    worksheet.write(table_row, 0, pricelist_product['code'] or "", format_bold_left)
                    worksheet.write(table_row, 1, pricelist_product['name'] or "", format_bold_left)
                    worksheet.write(table_row, 2, pricelist_product['uom'] or "", format_bold_center)
                    col = 3
                    if show_cost:
                        cost_price = format_currency_amount(pricelist_product['cost_price'],
                                                            request.env.company.currency_id)
                        worksheet.write(table_row, col, cost_price or "", format_bold_right)
                        col += 1
                    if show_qty_on_hand:
                        worksheet.write(table_row, col, pricelist_product['qty_available'] or "", format_bold_center)
                        col += 1

                    for pricelist, price in pricelist_product["price"].items():
                        worksheet.write(table_row, col, format_currency_amount(price, pricelist.currency_id),
                                        format_bold_right)
                        col += 1
                    table_row += 1
                    if pricelist_product.get("variants"):
                        variants = pricelist_product.get("variants")
                        for variant in variants:
                            worksheet.write(table_row, 0, variant['code'] or "")
                            worksheet.write(table_row, 1, variant['name'] or "")
                            worksheet.write(table_row, 2, variant['uom'] or "", format_center)
                            col = 3
                            if show_cost:
                                cost_price = format_currency_amount(variant['cost_price'],
                                                                    request.env.company.currency_id)
                                worksheet.write(table_row, col, cost_price or "", format_bold_right)
                                col += 1
                            if show_qty_on_hand:
                                worksheet.write(table_row, col, variant['qty_available'] or "",
                                                format_bold_center)
                                col += 1

                            for pricelist, price in variant["price"].items():
                                worksheet.write(table_row, col, format_currency_amount(price, pricelist.currency_id),
                                                format_right)
                                col += 1
                            table_row += 1

            else:
                for pricelist_product in values_to_render.get("products"):
                    worksheet.write(table_row, 0, pricelist_product['code'] or "")
                    worksheet.write(table_row, 1, pricelist_product['name'] or "")
                    worksheet.write(table_row, 2, pricelist_product['uom'] or "", format_center)
                    col = 3
                    if show_cost:
                        cost_price = format_currency_amount(pricelist_product['cost_price'],
                                                            request.env.company.currency_id)
                        worksheet.write(table_row, col, cost_price or "", format_bold_right)
                        col += 1
                    if show_qty_on_hand:
                        worksheet.write(table_row, col, pricelist_product['qty_available'] or "", format_bold_center)
                        col += 1
                    for pricelist, price in pricelist_product["price"].items():
                        worksheet.write(table_row, col, format_currency_amount(price, pricelist.currency_id),
                                        format_right)
                        col += 1
                    table_row += 1
        else:
            worksheet.merge_range(0, 0, 1, 6, "You do not have any products in the pricelist!", head_format_left)
        workbook.close()
        target_stream.seek(0)
        output = base64.encodebytes(target_stream.read())
        return output
