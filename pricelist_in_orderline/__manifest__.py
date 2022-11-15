# -*- coding: utf-8 -*-
{
    'name': "Sale Order Multiple Pricelist",

    'summary': """Use multiple pricelist in sale order""",

    'description': """In default sales module there is not any feature to use different multiple pricelists for a sale 
    order, so you can not set different pricelists in order line for the same order. This module gives you a smart 
    option to use different pricelist  in order line for the same order. No need to configure anything, Just install 
    and use.""",

    'author': "ErpMstar Solutions",
    'category': 'Sales',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'assets': {
        'web.assets_backend': [
            'pricelist_in_orderline/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'pricelist_in_orderline/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
    # 'images': ['static/description/banner.jpg'],
}
