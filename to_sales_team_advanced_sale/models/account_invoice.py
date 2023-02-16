from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    team_leader_id = fields.Many2one('res.users', string='Team Leader', compute='_compute_team', store=True)
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager', compute='_compute_team', store=True)
    crm_team_region_id = fields.Many2one('crm.team.region', string='Sales Region', compute='_compute_team', store=True, tracking=True)

    @api.depends('team_id')
    def _compute_team(self):
        for r in self:
            team_id = r.team_id
            vals = {}
            if team_id:
                if team_id.crm_team_region_id:
                    vals['crm_team_region_id'] = team_id.crm_team_region_id.id
                else:
                    vals['crm_team_region_id'] = False
                if team_id.regional_manager_id:
                    vals['regional_manager_id'] = team_id.regional_manager_id.id
                else:
                    vals['regional_manager_id'] = False
                if team_id.user_id:
                    vals['team_leader_id'] = team_id.user_id.id
                else:
                    vals['team_leader_id'] = False
            r.write(vals)
