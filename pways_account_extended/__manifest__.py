# -*- coding: utf-8 -*-
{
    'name': "LOT pos invoice report",
    'summary': "LOT pos invoice report",
    'description': "LOT pos invoice report",
    'author' : 'Preciseways',
    'website': "http://www.preciseways.com",
    'category': 'account',
    'version': '15.0.0',
    'depends': ['point_of_sale','stock_account' ,'product_expiry'],
    'data': ['views/invoice_report.xml'],
    'installable': True,
    'application': True,
    'currency': 'EUR',
    'license': 'OPL-1',

}
