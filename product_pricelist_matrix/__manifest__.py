# -*- coding: utf-8 -*-
{
    'name': "Product Pricelist Matrix",

    'summary': """Product Pricelist Matrix""",

    'description': """Product Pricelist Matrix view and print""",

    'author': 'ErpMstar Solutions',

    'category': 'Sales',
    'version': '1.3',
    # any module necessary for this one to work correctly
    'depends': ['sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'report/product_pricelist_report_templates.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'product_pricelist_matrix/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'product_pricelist_matrix/static/src/xml/**/*',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
}
