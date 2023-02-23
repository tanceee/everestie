# -*- coding: utf-8 -*-
{
    "name": "Invoice Report",
    "version": "15.0.0",
    'category': 'Generic Modules/Accounting',
    "depends": ['account', 'stock_account', 'sale_stock', 'point_of_sale', 'product_expiry', 'sale_management', 'dev_invoice_currency_rate'],
    "data": [
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
        'views/pos_config.xml',
        "report/report_action.xml",
        "report/template_tax_invoice.xml",
        "report/template_invoice_details.xml",
    ],
    'assets':{
        'point_of_sale.assets': [
            'pways_invoice_report/static/src/js/pos_models.js',
            'pways_invoice_report/static/src/js/pos_paymentScreen.js',
        ],
        'web.assets_qweb': [
            'pways_invoice_report/static/src/xml/PaymentScreen.xml',
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
