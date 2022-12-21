# -*- coding: utf-8 -*-
{
    'name': "Lot Expiry Invoice Report",
    'summary': "Lot Expiry Invoice Report",
    'description': "Lot Expiry Invoice Report",
    'author' : 'Preciseways',
    'website': "http://www.preciseways.com",
    'category': 'account',
    'version': '15.0.0',
    'depends': ['stock_account', 'sale_stock', 'sale_management'],
    'data': [
        'views/invoice_report.xml',
    ],
    
    'installable': True,
    'application': True,
    'currency': 'EUR',
    'license': 'OPL-1',

}
