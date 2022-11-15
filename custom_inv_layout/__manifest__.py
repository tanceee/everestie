# -*- coding: utf-8 -*-
{
    'name': "Custom Invoice layout",

    'summary': """Custom Invoice layout""",

    'description': """Custom Invoice layout""",

    'author': "ErpMstar Solutions",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/report_invoice_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,

}
