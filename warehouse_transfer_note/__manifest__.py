# -*- coding: utf-8 -*-
{
    'name': "Warehouse Transfer Note",

    'summary': """Warehouse Transfer Note""",

    'description': """
       Warehouse Transfer Note
    """,


    'author': 'ErpMstar Solutions',
    'category': 'Stock',
    'version': '1.0',


    # any module necessary for this one to work correctly
    'depends': ['fiscalization_base', 'stock', 'stock_operating_unit'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_sequence.xml',
        'report/report_stockpicking_operations.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': True,
}