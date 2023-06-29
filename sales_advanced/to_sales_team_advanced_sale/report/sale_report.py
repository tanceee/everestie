from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    team_leader_id = fields.Many2one('res.users', string='Team Leader', readonly=True)
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager', readonly=True)
    crm_team_region_id = fields.Many2one('crm.team.region', string='Sales Region', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields.update({
            'team_leader_id': ', team_leader.id AS team_leader_id',
            'regional_manager_id': ', regional_manager.id AS regional_manager_id',
            'crm_team_region_id': ', reg.id AS crm_team_region_id'
            })
        from_clause += """
        LEFT JOIN crm_team AS team ON team.id = s.team_id
        LEFT JOIN crm_team_region AS reg ON reg.id = s.crm_team_region_id
        LEFT JOIN res_users AS team_leader ON team_leader.id = s.team_leader_id
        LEFT JOIN res_users AS regional_manager ON regional_manager.id = s.regional_manager_id
        """
        groupby += ', team.id, reg.id, team_leader.id, regional_manager.id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
