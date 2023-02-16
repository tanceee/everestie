from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    regions = env['crm.team.region'].search([('user_id', '=', False)])
    if regions:
        regions = regions.sorted('parent_id')
        regions._compute_user_id()
