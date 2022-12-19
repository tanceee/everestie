# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Salesperson Own Customers Saleorders | Salesperson Own Customers | Salesperson Own Saleorders | Sale Person Own Customer Access | Sales Person Own Customer | Sale Person Own Sale Order | Sales Person Own Salesorder",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "license": "OPL-1",
    "support": "support@softhealer.com",
    "version": "15.0.1",
    "category": "Sales",
    "summary": "salesperson specific customer,Salesperson particular customer,Salesperson special customer,Salesperson particular Saleorder,Salesperson Own Sale Order,Salesperson Own SO,salesperson specific Sale Order,Salesperson permission for Own Customer Odoo",
    "description": """Currently, in odoo all customers and sale orders are visible to the salesperson, Our module will help to show only allocated customers to the salesperson and that allocated customer's sale orders are only visible to the salesperson.""",
    "depends": ["sh_sales_person_customer"],
    "data": [
        "security/sale_order_security.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "images": ["static/description/background.png", ],
    "price": "10",
    "currency": "EUR"
}
