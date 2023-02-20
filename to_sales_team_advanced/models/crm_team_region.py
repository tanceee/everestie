import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CRMTeamRegion(models.Model):
    _name = 'crm.team.region'
    _inherit = 'mail.thread'
    _description = 'Sales Region'

    @api.model
    def _get_manager_domain(self):
        return [('id', 'in', self.env.ref('to_sales_team_advanced.group_sale_regional_manager').users.ids)]

    name = fields.Char(string='Name', required=True, index=True)
    active = fields.Boolean(string='Active', default=True)
    user_id = fields.Many2one('res.users', string='Manager', compute='_compute_user_id', store=True, readonly=False,
                              tracking=True, domain=_get_manager_domain,
                              help="The one who manages sales operations and activities in this region")
    user_assistant_ids = fields.Many2many('res.users', 'sale_team_region_users_assistant_rel', 'region_id', 'user_id',
                                          string='Regional Manager Assistant', domain=_get_manager_domain,
                                          help="The ones who help the manager manage sales operations and activities in this region")

    team_ids = fields.One2many('crm.team', 'crm_team_region_id', string='Teams / Channels')
    member_ids = fields.Many2many('res.users', string='Sales Persons', compute='_compute_member_ids', store=True)
    display_member_ids = fields.Many2many('res.users', string='All Sales Persons', compute='_compute_display_member_ids')
    parent_id = fields.Many2one('crm.team.region', string='Parent Region', tracking=True, ondelete='cascade', help="The parent region to which this region belongs.")
    child_ids = fields.One2many('crm.team.region', 'parent_id', string='Child Regions')
    recursive_child_ids = fields.Many2many('crm.team.region', 'sale_team_region_recursive_children_rel', 'parent_id', 'child_id', string='Recursive Children',
                                           compute='_compute_recursive_child_ids', store=True, recursive=True,
                                           help="The recursive children of this sales region.")
    recursive_parent_ids = fields.Many2many('crm.team.region', 'sale_team_region_recursive_children_rel', 'child_id', 'parent_id', string='Recursive Parent',
                                            compute='_compute_recursive_parent_ids', readonly=True, recursive=True)

    recursive_user_ids = fields.Many2many('res.users', 'sale_team_region_recursive_manager_rel', 'region_id', 'user_id', string='Recursive Managers',
                                          compute='_compute_recursive_user_ids', store=True, recursive=True,
                                          help="The recursive managers of this sales region.")

    recursive_assistant_ids = fields.Many2many('res.users', 'sale_team_region_recursive_assistant_rel', 'region_id', 'user_id', string='Recursive Assistants',
                                          compute='_compute_recursive_assistant_ids', store=True, recursive=True,
                                          help="The recursive assistant of this sales region.")

    def _get_user_id(self):
        """
        Recursively search for user_id among the current record and its parents
        """
        if self.user_id:
            return self.user_id
        elif self.parent_id:
            return self.parent_id._get_user_id()
        else:
            return self.env['res.users']

    @api.depends('parent_id')
    def _compute_user_id(self):
        for r in self:
            r.user_id = r._get_user_id()

    @api.constrains('parent_id', 'child_ids')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive region.'))
        return True

    def _get_recursive_children(self):
        child_ids = self.mapped('child_ids')
        for child_id in child_ids:
            child_ids |= child_id._get_recursive_children()
        return child_ids

    def _get_recursive_parents(self):
        parents = self.parent_id
        for parent in parents:
            parents |= parent._get_recursive_parents()
        return parents

    @api.depends('child_ids', 'child_ids.recursive_child_ids')
    def _compute_recursive_child_ids(self):
        for r in self:
            r.recursive_child_ids = r._get_recursive_children()

    @api.depends('parent_id', 'parent_id.recursive_parent_ids')
    def _compute_recursive_parent_ids(self):
        for r in self:
            r.recursive_parent_ids = r._get_recursive_parents()

    @api.depends('recursive_parent_ids', 'user_id', 'parent_id.recursive_user_ids')
    def _compute_recursive_user_ids(self):
        for r in self:
            recursive_user_ids = r.user_id
            recursive_user_ids |= r.recursive_parent_ids.mapped('user_id')
            r.recursive_user_ids = recursive_user_ids

    def _get_recursive_assistants(self):
        recursive_assistants = self.user_assistant_ids
        for parent in self.parent_id:
            if parent.user_assistant_ids:
                recursive_assistants |= parent._get_recursive_assistants()
        return recursive_assistants

    @api.depends('user_assistant_ids', 'parent_id.user_assistant_ids')
    def _compute_recursive_assistant_ids(self):
        for r in self:
            r.recursive_assistant_ids = r._get_recursive_assistants()

    def _get_all_members(self):
            member_ids = self.team_ids.member_ids
            member_ids |= self.team_ids.user_id
            return member_ids

    @api.depends('team_ids', 'team_ids.member_ids')
    def _compute_member_ids(self):
        for r in self:
            r.member_ids = r._get_all_members()

    @api.depends('team_ids', 'team_ids.member_ids')
    def _compute_display_member_ids(self):
        for r in self:
            r.display_member_ids = r._get_all_members()

    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        res = super(CRMTeamRegion, self).create(vals_list)
        self.env['ir.rule'].clear_caches()
        return res

    def write(self, vals):
        res = super(CRMTeamRegion, self).write(vals)
        self.env['ir.rule'].clear_caches()
        return res

    def unlink(self):
        res = super(CRMTeamRegion, self).unlink()
        self.env['ir.rule'].clear_caches()
        return res
