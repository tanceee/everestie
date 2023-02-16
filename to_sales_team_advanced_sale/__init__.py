from odoo import api, SUPERUSER_ID

from . import models
from . import report


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    config_menu = env.ref('sale.menu_sale_config')
    leader_group =  env.ref('to_sales_team_advanced.group_sale_team_leader')
    if config_menu and leader_group:
        config_menu.groups_id = [(3, leader_group.id, 0)]
