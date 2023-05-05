# See LICENSE file for full copyright and licensing details.

{
    'name': 'Lot Expiry Extended',
    'version': '15.0.1.0.0',
    'summary': """Lot Expiry date in outgoing picking""",
    'description': """Lot Expiry date in outgoing picking""",
    'depends': ['sale_stock', 'sale_management', 'product_expiry'],
    'data': ["views/product_views.xml",],
    'auto_install': False,
    'installable': True,
    'application': True,
}
