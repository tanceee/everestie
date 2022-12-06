# -*- coding: utf-8 -*-

{
    'name': 'PoS Cash In-Out Partner/ Cash Move Partner',
    'author': 'Odoo Bin',
    'company': 'Odoo Bin',
    'maintainer': 'Odoo Bin',
    'description': """ PoS Cash In-Out Partner, Cash in out partner, cash move partner, cash move customer, cash move contact, 
    cash in customer, cash in contact, cash in user, cash move customer, cash move contact, cash out contact,
    cash out customer, cash out partner""",
    'summary': """This module allow you to select cash in-out partner/contact during cash move in point of sale interface
""",
    'version': '15.0',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'category': 'Point of Sale',
    'demo': [],
    'assets': {
            'point_of_sale.assets': [
                'ob_pos_cash_in_out_partner/static/src/js/CashMoveButton.js',
                'ob_pos_cash_in_out_partner/static/src/js/CashMovePopup.js',
            ],
            'web.assets_qweb': [
                'ob_pos_cash_in_out_partner/static/src/xml/**/*',
            ],
    },
    'live_test_url': 'https://youtu.be/3tFvYsq9Of0',
    'images': ['static/description/banner.png'],
    "price": 5.99,
    "currency": 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
}
