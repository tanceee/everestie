# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api


class UpdateSalesPerson(models.TransientModel):

    _name = "sh.res.partner.mass.update.wizard"
    _description = "Mass Update Wizard"

    res_partner_ids = fields.Many2many('res.partner')
    update_salesperson_bool = fields.Boolean(string="Update Sales Person",
                                             default=False)
    sales_person = fields.Many2one('res.users', string='Sales Person')
    update_allocate_sales_person_bool = fields.Boolean(
        string="Update Allocate SalesPersons", default=False)
    update_allocate_salesperson_ids = fields.Many2many(
        'res.users', string='Allocate Salesperson')
    update_method_allocate_sales_person = fields.Selection([
        ("add", "Add"),
        ("replace", "Replace"),
    ],
        default="add", string='Allocate Salesperson Type')

    def update_record(self):
        if self.update_salesperson_bool == True:
            self.res_partner_ids.write({'user_id': self.sales_person.id})

        if self.update_method_allocate_sales_person == 'add':
            for i in self.update_allocate_salesperson_ids:
                self.res_partner_ids.write({'sales_persons_ids': [(4, i.id)]})

        if self.update_method_allocate_sales_person == 'replace':
            self.res_partner_ids.write(
                {'sales_persons_ids': [(6, 0, self.update_allocate_salesperson_ids.ids)]})
