from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    team_leader_id = fields.Many2one('res.users', string='Team Leader', readonly=True)
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager', readonly=True)
    crm_team_region_id = fields.Many2one('crm.team.region', string='Sales Region', readonly=True)

    def _select(self):
        sql = super(AccountInvoiceReport, self)._select()
        sql += """,
        inv_team_leader.id AS team_leader_id,
        inv_regional_manager.id AS regional_manager_id,
        tr.id AS crm_team_region_id"""
        return sql

    def _from(self):
        sql = super(AccountInvoiceReport, self)._from()
        sql += """
            LEFT JOIN crm_team AS t ON t.id = move.team_id
            LEFT JOIN crm_team_region AS tr ON tr.id = move.crm_team_region_id
            LEFT JOIN res_users AS inv_team_leader ON inv_team_leader.id = move.team_leader_id
            LEFT JOIN res_users AS inv_regional_manager ON inv_regional_manager.id = move.regional_manager_id
        """
        return sql

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", tr.id, inv_regional_manager.id, inv_team_leader.id"
