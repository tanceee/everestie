from odoo.tests import common


class TestDefaultTeamCommon(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Set up data for default team tests."""
        super(TestDefaultTeamCommon, cls).setUpClass()

        cls.no_mailthread_features_ctx = {
            'no_reset_password': True,
            'tracking_disable': True,
        }
        cls.env = cls.env(context=dict(cls.no_mailthread_features_ctx, **cls.env.context))

        cls.CrmTeam = cls.env['crm.team']
        ResUsers = cls.env['res.users']
        group_sale_manager = cls.env.ref('sales_team.group_sale_manager')
        cls.user = ResUsers.create({
            'name': 'Team User',
            'login': 'sales_team_user',
            'email': 'sales.team.user@example.viindoo.com',
            'groups_id': [(6, 0, [group_sale_manager.id])]
        })
        cls.team_1 = cls.env['crm.team'].create({
            'name': 'Test Team',
            'member_ids': [(4, cls.user.id)],
            'company_id': False
        })
        # Europe Team (fall back  team)
        cls.team_2 = cls.env['crm.team'].create({
            'name': 'Team 2',
            'sequence': 2,
            'company_id': False
        })
        cls.team_3 = cls.env['crm.team'].create({
            'name': 'Team 3',
            'sequence': 2,
            'company_id': False
        })

        cls.user_1 = ResUsers.create({
            'name': 'user_1',
            'login': 'user_1_test_sales_team_advanced',
            'email': 'm.u0@example.viindoo.com',
        })
        cls.user_2 = cls.user_1.copy({'name': 'user_2'})
        cls.user_3 = cls.user_2.copy({'name': 'user_3'})
        cls.CRMregion = cls.env['crm.team.region']
        cls.sale_rg_1 = cls.CRMregion.create({
            'name': 'sale_rg_1',
            'user_id': cls.user_1.id,
        })
        cls.sale_rg_2 = cls.CRMregion.create({
            'name': 'sale_rg_2'
        })
        cls.sale_rg_3 = cls.CRMregion.create({
            'name': 'sale_rg_3'
        })
        cls.team_1.write({
            'member_ids': [(4, cls.user_1.id), (4, cls.user_2.id)],
        })
        cls.team_2.write({
            'member_ids': [(4, cls.user_3.id)],
        })
