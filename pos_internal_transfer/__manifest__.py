# -*- coding: utf-8 -*-

{
    'name': 'POS Internal Transfer',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'ErpMstar Solutions',
    'summary': 'Allows you to transfer internal picking from POS.',
    'description': "Allows you to transfer internal picking from POS.",
    'depends': ['point_of_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_internal_transfer/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'pos_internal_transfer/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/popup.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 10,
    'currency': 'EUR',
}
