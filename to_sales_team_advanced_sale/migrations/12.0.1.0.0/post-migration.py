from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_invoice_ids = env['account.invoice'].search([])

    for team_id in all_invoice_ids.mapped('team_id'):
        all_invoice_ids.filtered(lambda l: l.team_id == team_id).write({
            'team_leader_id': team_id.user_id and team_id.user_id.id or False,
            'regional_manager_id': team_id.regional_manager_id and team_id.regional_manager_id.id or False,
            'crm_team_region_id': team_id.crm_team_region_id and team_id.crm_team_region_id.id or False
            })

    all_so_ids = env['sale.order'].search([])
    for team_id in all_so_ids.mapped('team_id'):
        all_so_ids.filtered(lambda l: l.team_id == team_id).write({
            'team_leader_id': team_id.user_id and team_id.user_id.id or False,
            'regional_manager_id': team_id.regional_manager_id and team_id.regional_manager_id.id or False,
            'crm_team_region_id': team_id.crm_team_region_id and team_id.crm_team_region_id.id or False
            })
