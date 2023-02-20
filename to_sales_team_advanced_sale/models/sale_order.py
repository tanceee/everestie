from odoo import models, fields, api
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # override fields ``user_id` & `team_id` to add condition
    user_id = fields.Many2one(domain="[('id', 'in', users_can_change)]")
    team_id = fields.Many2one(domain="[('id', 'in', teams_can_change)]")
    users_can_change = fields.Many2many('res.users', compute='_compute_users_can_change', compute_sudo=True)
    teams_can_change = fields.Many2many('crm.team', compute='_compute_teams_can_change', compute_sudo=True)
    team_leader_id = fields.Many2one('res.users', string='Team Leader', compute='_compute_team_id', store=True)
    crm_team_region_id = fields.Many2one('crm.team.region', string='Sales Region', compute='_compute_crm_team_region_id', store=True)
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager', compute='_compute_regional_manager_id', store=True)

    @api.depends('team_id')
    def _compute_users_can_change(self):
        user = self.user_id
        if user.has_group('sales_team.group_sale_salesman_all_leads'):
            domain = []
        else:
            members = user | (user.sales_region_assistant_ids | user.sales_region_manager_ids).member_ids | user.sales_team_manager_ids.member_ids
            if user.has_group('to_sales_team_advanced.group_sale_team_leader'):
                # other members of the team if the user is also a member of the team
                members |= user.crm_team_member_ids.crm_team_id.member_ids
            domain = [('id', 'in', members.ids)]
        for r in self:
            # combined with the default domain of the `CRM` module
            default_domain = [('groups_id', '=', self.env.ref("sales_team.group_sale_salesman").id),
                              ('share', '=', False), ('company_ids', '=', r.company_id.id)]
            domain = expression.AND([domain, default_domain])
            r.users_can_change = self.env['res.users'].search(domain)

    @api.depends('user_id')
    def _compute_teams_can_change(self):
        user = self.user_id
        teams = user.sales_team_manager_ids | user.crm_team_ids | (user.sales_region_assistant_ids | user.sales_region_manager_ids).team_ids
        if self.user_has_groups('sales_team.group_sale_salesman_all_leads'):
            domain = []
        else:
            domain = [('id', 'in', teams.ids)]
        for r in self:
            # combined with the default domain of the `CRM` module
            default_domain = ['|', ('company_id', '=', False), ('company_id', '=', r.company_id.id)]
            domain = expression.AND([domain, default_domain])
            r.teams_can_change = self.env['crm.team'].search(domain)

    @api.depends('team_id')
    def _compute_team_id(self):
        for r in self:
            r.team_leader_id = r.team_id.user_id.id

    @api.depends('team_id', 'user_id')
    def _compute_crm_team_region_id(self):
        for r in self:
            if r.team_id:
                r.crm_team_region_id = r.team_id.crm_team_region_id.id
            elif not r.crm_team_region_id:
                r.crm_team_region_id = r.user_id.sales_region_manager_ids[:1] or r.user_id.sales_region_assistant_ids[:1]
            else:
                r.crm_team_region_id = r.crm_team_region_id

    @api.depends('crm_team_region_id')
    def _compute_regional_manager_id(self):
        for r in self:
            r.regional_manager_id = r.crm_team_region_id.user_id

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        update_data = {}
        if self.crm_team_region_id:
            update_data['crm_team_region_id'] = self.crm_team_region_id
        if self.regional_manager_id:
            update_data['regional_manager_id'] = self.regional_manager_id.id
        if self.team_leader_id:
            update_data['team_leader_id'] = self.team_leader_id.id
        if bool(update_data):
            invoice_vals.update(update_data)
        return invoice_vals
