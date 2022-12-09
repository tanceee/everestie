{
    'name': 'POS Serial Lot Selection',
    'version': '15.0',
    'category': 'Point of Sale',
    'author': 'Preciseways',
    'website': 'www.preciseways.com',
    'summary': 'All allocated serials or lots are avaiable in pos screen for that particular product. as per cart qty you only need to select that lot or serial.',
    'description': 'All allocated serials or lots are avaiable in pos screen for that particular product. as per cart qty you only need to select that lot or serial.',
    'depends': ['point_of_sale', 'product_expiry'],
    'assets': {
        'point_of_sale.assets': [
            'pways_pos_lot_selection/static/src/js/*',
            'pways_pos_lot_selection/static/src/js/**/*',
            'pways_pos_lot_selection/static/src/css/*',
        ],
        'web.assets_qweb': [
            'pways_pos_lot_selection/static/src/xml/*',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'OPL-1',
    'price': 15,
    'currency': 'EUR',
    'images':['static/description/banner.png'],
    'live_test_url': 'https://preciseways.com',
}
