from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    # override `crm_team_member_ids` field to set context: active_test = True
    # for unknown reasons, when accessing from SO, the context value `active_test = False` should cause some access rules to fail
    # Also, by default odoo, does not set context in this field, so can be interpreted `active_test = True`
    # TODO: re-check in 16.0+
    crm_team_member_ids = fields.One2many(context={'active_test': True})
    sales_team_manager_ids = fields.One2many('crm.team', 'user_id', string='Sales Team Manager')
    sales_region_manager_ids = fields.One2many('crm.team.region', 'user_id', string='Sales Region Direct Manager')
    sales_region_assistant_ids = fields.Many2many('crm.team.region', 'sale_team_region_users_assistant_rel', 'user_id', 'region_id',
                                                    string='Sales Region Assistant')
