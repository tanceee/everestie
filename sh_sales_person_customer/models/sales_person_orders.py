# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    sales_persons_ids = fields.Many2many(
        "res.users",
        string="Allocate Sales Persons"
    )

    def action_sales_person_customer_update(self):
        return {
            'name':
            'Mass Update',
            'res_model':
            'sh.res.partner.mass.update.wizard',
            'view_mode':
            'form',
            'context': {
                'default_res_partner_ids':
                [(6, 0, self.env.context.get('active_ids'))]
            },
            'view_id':
            self.env.ref(
                'sh_sales_person_customer.sh_res_partner_update_wizard_form_view').
            id,
            'target':
            'new',
            'type':
            'ir.actions.act_window'
        }

    # To apply domain to customer search

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        search_domain = [("name", operator, name)]

        if(
            self.env.user.has_group("sales_team.group_sale_salesman") and not
            (self.env.user.has_group("sales_team.group_sale_salesman_all_leads"))
        ):
            search_domain = ["|", "|","|",
                             ("sales_persons_ids", "in", self.env.user.id),
                             ("user_id", "=", self.env.user.id),
                             ("id", "=", self.env.user.partner_id.id),
                             ("employee_ids","!=",False)
                             ]
        partners = self.search(search_domain)
        return partners.name_get()

    # To apply domain to menu action
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        _ = self._context or {}
        if(
            self.env.user.has_group("sales_team.group_sale_salesman") and not
            (self.env.user.has_group("sales_team.group_sale_salesman_all_leads"))
        ):
            args += ["|", "|","|",
                     ("sales_persons_ids", "in", self.env.user.id),
                     ("user_id", "=", self.env.user.id),
                     ("id", "=", self.env.user.partner_id.id),
                     ("employee_ids","!=",False)
                     ]
        return super(ResPartner, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
        )

    @api.model
    def default_get(self, fields):
        vals = super(ResPartner, self).default_get(fields)

        if self.env.user:
            vals.update({
                "user_id": self.env.user.id,
                "sales_persons_ids": [(6, 0, [self.env.user.id])]
            })

        return vals
