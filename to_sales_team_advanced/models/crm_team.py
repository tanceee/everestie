import threading

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    def get_leader_domain(self):
        return [('id', 'in', self.env.ref('to_sales_team_advanced.group_sale_team_leader').users.ids)]

    # override `user_id` field to set domain
    user_id = fields.Many2one(domain=get_leader_domain)
    
    # override `crm_team_member_ids` field to set context: active_test = True
    # for unknown reasons, when accessing from SO, the context value `active_test = False` should cause some access rules to fail
    # Also, by default odoo, does not set context in this field, so can be interpreted `active_test = True`
    # TODO: re-check in 16.0+
    crm_team_member_ids = fields.One2many(context={'active_test': True})
    
    crm_team_region_id = fields.Many2one('crm.team.region', string='Region', tracking=True, help="The region to which this sales team belongs")
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager',
                                          compute='_compute_regional_manager_id', store=True, tracking=True,
                                          help="The one who has the rights to approve sales targets"
                                          " for the team and the team members")

    def _get_default_team_id(self, user_id=None, domain=None):
        test_mode = getattr(threading.current_thread(), 'testing', False)

        user = self.env['res.users'].browse(user_id)
        if not user.sale_team_id and user.has_group('to_sales_team_advanced.group_sale_regional_manager') and not test_mode:
            return self.env['crm.team']
        return super(CrmTeam, self)._get_default_team_id(user_id=user_id, domain=domain)

    @api.depends('crm_team_region_id', 'crm_team_region_id.user_id')
    def _compute_regional_manager_id(self):
        for r in self:
            r.regional_manager_id = r.crm_team_region_id._get_user_id()

    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        res = super(CrmTeam, self).create(vals_list)
        self.env['ir.rule'].clear_caches()
        return res

    def write(self, vals):
        if self.check_access_rights('write', raise_exception=False):
            self.check_access_rule('write')
            if any(item in vals for item in ['crm_team_region_id', 'member_ids']):
                if not self.env.user.has_group('to_sales_team_advanced.group_sale_regional_manager'):
                    raise UserError(_("You don't have the rights to do this action. "
                                      "Only the members of the group `%s` can do it.") % self.env.ref('to_sales_team_advanced.group_sale_regional_manager').name)
            res = super(CrmTeam, self.sudo()).write(vals)
        else:
            res = super(CrmTeam, self).write(vals)
        self.env['ir.rule'].clear_caches()
        return res

    def unlink(self):
        res = super(CrmTeam, self).unlink()
        self.env['ir.rule'].clear_caches()
        return res
