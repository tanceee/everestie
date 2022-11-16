# -*- coding: utf-8 -*-
{
    'name': "SW - Multi Currency Partner Ledger",
    'summary': """Partner Ledger report catering for multiple currency transactions""",
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway.co",
    'license':  "Other proprietary",
    'category': 'Accounting',
    'version': '1.3',
    'depends': ['base', 'account'],
    'data': ['wizard/account_report_partner_ledger_view.xml',
             'report/report_partnerledger.xml',
             'security/ir.model.access.csv'],
    'installable': True
}
