# -*- coding: utf-8 -*-
{
    'name': "Skip POS Fiscalization",

    'summary': """Skip POS Fiscalization""",

    'description': """Skip POS Fiscalization""",

    'author': "ErpMstar Solutions",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Fiscalization',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['fiscalization'],
    'assets': {
        'point_of_sale.assets': [
            "skip_pos_fiscalization/static/src/js/pos.js"
        ],
        'web.assets_qweb': [
            "skip_pos_fiscalization/static/src/xml/pos.xml"
        ]
    },
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'application': True
}
