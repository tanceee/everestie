{
    'name': 'Include, Exclude or Edit Landed Cost to Product',
    'version': '15.0.1',
    'category': 'Purchase',
    'summary': 'Extend the Functionality of Landed Cost to Include or Exclude any product in valuation of Landed Cost.',
    'description': 'This Application Extend the Functionality of Landed Cost to Include or Exclude any product in valuation of Landed Cost. And it has Option to edit landed cost price based on your own Calculation.',
    
    'author': 'TeamUp4Solutions, TaxDotCom',
    'website': "http://www.taxdotcom.com",
    'maintainer': 'Sohail Ahmad, Younas',
    
    'depends': ['stock_landed_costs'],
    
    'data': ['security/ir.model.access.csv',
            'views/landed_cost.xml',
        ],
    
    'installable': True,
    'auto_install': False,
    'images': ['static/description/image.png'],
    'license': 'AGPL-3',
}
