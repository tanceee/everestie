# -*- coding: utf-8 -*-
{
    'name': "Sale Order Line Quick Add",

    'summary': """Sale Order Line Quick Add""",

    'description': """Sale Order Line Quick Add""",

    'author': "ErpMstar Solutions",
    'category': 'Sale',
    'version': '1.2',

    # any module necessary for this one to work correctly
    'depends': ['sale_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'wizards/quick_add_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': True,
}
