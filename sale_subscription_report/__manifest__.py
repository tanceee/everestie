# -*- coding: utf-8 -*-
{
    'name': "Sale Subscription Report",

    'summary': """Sale Subscription Report""",

    'description': """Sale Subscription Report""",

    'author': 'ErpMstar Solutions',
    'category': 'Sales/Subscriptions',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_subscription'],

    # always loaded
    'data': [
        'report/subscription_report.xml',
        'report/subscription_report_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
}
