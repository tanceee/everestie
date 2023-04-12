# -*- coding: utf-8 -*-
{
    'name': "Fiscalization Base",

    'summary': """Base Module for E-Invoice Fiscalization""",

    'description': """
        Base Module for E-Invoice Fiscalization
    """,

    'author': 'ErpMstar Solutions',
    'category': 'Invoice',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['operating_unit', 'base_iso3166', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
}
