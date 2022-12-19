# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Salesperson Own Customers",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "version": "15.0.2",
    "category": "Sales",
    "summary": """
salesperson specific customer, vendor see particular customer,
special customer salesperson customer seller get particular client Odoo
""",
    "description": """
Currently in odoo all customers are visible to salesperson,
For this our module will help to show only specific customers to salesperson.
""",
    "depends": ["sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/sales_person_orders.xml",
        "views/mass_customer_update_action.xml",
        "views/mass_salesperson_update_wizard_view.xml",
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "19",
    "currency": "EUR"
}
