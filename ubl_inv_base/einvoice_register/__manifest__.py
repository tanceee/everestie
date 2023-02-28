# -*- coding: utf-8 -*-
{
    'name': "E-Invoice Register",

    'summary': """Register E-Invoice on the tax server""",

    'description': """
        Register E-Invoice on the tax server
    """,

    'author': 'ErpMstar Solutions',
    'category': 'Invoice',
    'version': '1.5',

    # any module necessary for this one to work correctly
    'depends': ['ubl_inv_base', 'dev_invoice_currency_rate', "account_tax_unece", 'fiscalization_base',
                'account_operating_unit',
                'base_iban', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/report_invoice.xml',
        'views/templates.xml',
        'data/ir_sequence.xml',
        'views/views.xml',
        'views/res_config_settings_view.xml',
        'wizards/seller_inv_wizard_views.xml',
        'wizards/account_move_reversal_wizard_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'assets': {

        'web.assets_backend': ["/einvoice_register/static/src/js/url_action.js"]
    },
    'installable': True,
    'application': True,
}
