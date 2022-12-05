# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.
{
    "name": "POS Default Invoice | Point Of Sale Default Invoice",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point Of Sale",
    "summary": "Point Of Sale Default Invoices, POS Default Invoice, Default Invoice on POS, Point Of Sale Bydefault Invoice, POS Bydefault Invoice, POS Invoices Odoo",
    "description": """This module activates the invoice button by default in the POS. Here the invoice button is selected so when an order placed invoice generates automatically.""",
    "version": "15.0.1",
    "depends": ['base', 'point_of_sale'],
    "application": True,
    "data": [
        'views/pos_config_settings.xml',
    ],
    'assets': {'point_of_sale.assets': ['sh_pos_default_invoice/static/src/js/pos.js',]},
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": 20,
    "currency": "EUR"
}
