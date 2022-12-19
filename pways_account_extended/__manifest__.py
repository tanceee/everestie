# -*- coding: utf-8 -*-
{
    'name': "Pways invoice report",
    'summary': "Pways invoice report",
    'description': "Pways invoice report",
    'author' : 'Preciseways',
    'website': "http://www.preciseways.com",
    'category': 'account',
    'version': '15.0.0',
    'depends': ['account', 'stock_account', 'sale_stock'],
    'data': [
        'views/invoice_report.xml',
    ],
    
    'installable': True,
    'application': True,
    'price': 15.0,
    'currency': 'EUR',
    'license': 'OPL-1',

}
