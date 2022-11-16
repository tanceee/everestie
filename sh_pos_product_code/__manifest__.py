# Part of Softhealer Technologies.

{
    'name': 'POS Product Internal Reference',
    "author": "Softhealer Technologies",
    "website": "http://www.softhealer.com",
    "support": "support@softhealer.com",
    'version': '15.0.2',
    "license": "OPL-1",
    'category': 'Point of Sale',
    "summary": "Product Internal Reference Code On POS, POS Internal Reference Number App, Display Point Of Sale Ref No Module, POS Internal Reference Code, POS Ref Code On Screen, Find POS Product By Ref No Odoo",
    "description": """This module shows the internal reference number/code of products in the POS(Point Of Sale) screen. Using this module users can find the product easily in POS.
 Product Internal Reference Code On POS Odoo
 Show Internal Reference On POS Module, Display Point Of Sale Reference No, POS Internal Reference Code, POS Ref Code On Screen, Find POS Product  By Ref No, POS Internal Reference Number On Screen Odoo.
 POS Internal Reference Number App, Display Point Of Sale Ref No Module, POS Internal Reference Code, POS Ref Code On Screen, Find POS Product By Ref No Odoo """,
    'depends': ['point_of_sale', 'product'],
    'data': ['views/pos_view.xml'],
    'assets': {'point_of_sale.assets': ['sh_pos_product_code/static/src/js/pos.js',],
               'web.assets_qweb': ['sh_pos_product_code/static/src/xml/product_screen.xml', ]},
    'images': ['static/description/background.png', ],
    'installable': True,
    "price": 15,
    "currency": "EUR"
}
