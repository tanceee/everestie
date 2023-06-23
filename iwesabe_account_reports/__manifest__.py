# -*- coding: utf-8 -*-
##############################################################################
#
#    Global Creative Concepts Tech Co Ltd.
#    Copyright (C) 2018-TODAY iWesabe (<https://www.iwesabe.com>).
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Account Reports Sales Person Filter",
    'summary': """iWesabe Account Reports Person Filter """,
    'description': """
        This module for Accounting Enterprise Reports Person Filter.
    """,
    'author': "iWesabe",
    'website': "https://www.iwesabe.com/",
    'license': 'OPL-1',
    'category': 'Sales/',
    'version': '15.0.1',

    'depends': ['account','account_accountant','account_reports'],

    'data': [
        'views/template_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'iwesabe_account_reports/static/src/js/custom_account_reports.js'
        ],
        
    },
    'images': ['static/description/banner.png'],

    'demo': [],

    'installable': True,
    'auto_install': False,
}
