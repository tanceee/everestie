# -*- coding: utf-8 -*-
{
    'name': 'OS Disable Quick Create',
    'version': '15.0.1.0.0',
    'author': 'Omega System',
    'maintainer': 'Omega System',
    'website': 'https://omegasystem.in/',
    'license': 'AGPL-3',
    'category': 'Web',
    'summary': 'Disable "quick create" for all and "create and edit" '
               'for specific models',
    'depends': [
        'web',
        'base'
    ],
    'data': [
        'views/ir_model.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/os_disable_quick_create/static/src/js/disable_quick_create.js'],
    },
    'images': ['static/description/banner.png'],
    'price': 10.00,
    'currency': 'EUR',
    'installable': True,
    'application': True,
}
