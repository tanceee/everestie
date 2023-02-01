# -*- coding: utf-8 -*-

{
    'name': 'Pos Operating Unit',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'ErpMstar Solutions',
    'summary': 'Allows you to create multiple operating units in POS.',
    'description': "Allows you to create multiple operating units in POS.",
    'depends': ['point_of_sale','operating_unit'],
    'data': [
        'views/views.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/line.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 20,
    'currency': 'EUR',
}
