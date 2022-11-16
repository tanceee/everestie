# -*- coding: utf-8 -*-
# Copyright 2020 CorTex IT Solutions Ltd. (<https://cortexsolutions.net/>)
# License OPL-1

{
    'name': "Remove Decimal Zero Trailing",

    'summary': """
        This module enable you to remove decimal zero trailing in all Odoo views and reports.
        """,
    'description': """
Remove Decimal Zero Trailing
odoo Decimal Precision
Decimal Precision
Decimal Precision drop zeros
Hide Decimal Zero Trailing
    """,

    'author': 'CorTex IT Solutions Ltd.',
    'website': 'https://cortexsolutions.net',
    'license': 'OPL-1',
    'support': 'support@cortexsolutions.net',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': [ 'base'],
    # always loaded
    'data': [

    ],
    'assets': {
        'web.assets_backend': [
            'remove_decimal_zero_trailing/static/src/js/field_utils.js',
            ]
    },
    'images': ['static/description/main_screenshot.png'],
    "installable": True
}
