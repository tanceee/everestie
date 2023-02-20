from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.to_sales_team_advanced.tests.test_default_team import TestDefaultTeamCommon


@tagged('post_install', '-at_install')
class TestSalesTeamAdvancedSaleSecurity(TestDefaultTeamCommon):

    @classmethod
    def setUpClass(cls):
        super(TestSalesTeamAdvancedSaleSecurity, cls).setUpClass()

        cls.user_4 = cls.user_1.copy({'name': 'user_4', 'login': 'user_4'})
        cls.team_1.member_ids = [(4, cls.user_4.id)]

        cls.user_5 = cls.user_1.copy({'name': 'user_5', 'login': 'user_5', 'sale_team_id': False})
        cls.team_3.user_id = cls.user_5

        cls.team_1.crm_team_region_id = cls.sale_rg_1
        cls.team_2.crm_team_region_id = cls.sale_rg_1
        cls.team_3.crm_team_region_id = cls.sale_rg_2

        cls.sale_order_1 = cls.env['sale.order'].create({
            'partner_id': cls.user_1.partner_id.id,
            'note': 'Invoice after delivery',
            'payment_term_id': cls.env.ref('account.account_payment_term_end_following_month').id,
            'user_id': cls.user_1.id,
            'team_id': cls.team_1.id,
        })
        cls.sale_order_2 = cls.env['sale.order'].create({
            'partner_id': cls.user_2.partner_id.id,
            'note': 'Invoice after delivery',
            'payment_term_id': cls.env.ref('account.account_payment_term_end_following_month').id,
            'user_id': cls.user_3.id,
            'team_id': cls.team_2.id,
        })
        cls.sale_order_3 = cls.env['sale.order'].create({
            'partner_id': cls.user_3.partner_id.id,
            'note': 'Invoice after delivery',
            'payment_term_id': cls.env.ref('account.account_payment_term_end_following_month').id,
            'user_id': cls.user_4.id,
            'team_id': cls.team_1.id,
        })
        cls.sale_order_4 = cls.env['sale.order'].create({
            'partner_id': cls.user_3.partner_id.id,
            'note': 'Invoice after delivery',
            'payment_term_id': cls.env.ref('account.account_payment_term_end_following_month').id,
            'user_id': False,
            'team_id': False,
        })
        cls.sale_order_5 = cls.env['sale.order'].create({
            'partner_id': cls.user_3.partner_id.id,
            'note': 'Invoice after delivery',
            'payment_term_id': cls.env.ref('account.account_payment_term_end_following_month').id,
            'user_id': cls.user_5.id,
            'team_id': cls.team_3.id,
        })

    def test_3000_group_sale_team_leader_member(self):
        """ user_2 has group_sale_team_leader and is member of team_1
            user_2 can read, write, change state all document of team_1
            user_2 can't read, write, unlink, change state all document of another team """

        self.user_1.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_team_leader').ids)]
        self.user_2.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_team_leader').ids)]
        self.user_3.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]
        self.user_4.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]

        # SO created by team leader
        self.team_1.user_id = self.user_1
        so_team_1 = self.sale_order_1.with_user(self.user_2)
        so_team_1.read([])
        so_team_1.write({'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO created by salesman
        so_team_1 = self.sale_order_3.with_user(self.user_2)
        so_team_1.read([])
        so_team_1.write({'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO without salesperson and team
        so_without_user = self.sale_order_4.with_user(self.user_2)
        so_without_user.read([])
        so_without_user.write({'state': 'cancel'})
        self.assertRaises(AccessError, so_without_user.unlink)

        # SO created by user belong another team
        so_team_2 = self.sale_order_2.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_2.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_2.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_2.unlink)

    def test_3001_group_sale_team_leader_leader(self):
        """ user_1 has group_sale_team_leader and is leader of team_1
            user_1 can read, write, change state all document of team_1
            user_1 can't read, write, unlink, change state all document of another team """

        self.user_2 = self.user_1
        self.test_3000_group_sale_team_leader_member()

    def region_test_common(self):
        self.user_1.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_2.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_3.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_team_leader').ids)]
        self.user_4.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]
        self.user_5.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]

        self.team_1.crm_team_region_id = self.sale_rg_1
        self.team_2.crm_team_region_id = self.sale_rg_1

        # SO created by region manager team 1
        so_team_1 = self.sale_order_1.with_user(self.user_2)
        so_team_1.read([])
        so_team_1.write({'state': 'cancel'})
        so_team_1.unlink()

        # SO created by salesman team 1
        so_team_1 = self.sale_order_3.with_user(self.user_2)
        so_team_1.read([])
        so_team_1.write({'state': 'cancel'})
        so_team_1.unlink()

        # SO without salesperson, team, region
        so_without_user = self.sale_order_4.with_user(self.user_2)
        so_without_user.read([])
        so_without_user.write({'state': 'cancel'})
        so_without_user.unlink()

        # SO created leader of other team but belong region 1
        so_team_2 = self.sale_order_2.with_user(self.user_2)
        so_team_2.read([])
        so_team_2.write({'state': 'cancel'})
        so_team_2.unlink()

    def test_3003_group_sale_regional_manager_direct(self):
        """ user_1 has group_sale_regional_manager
            user_1 is direct regional manager of team_1
            user_1 has all permission in regional that team_1 belongs"""

        self.sale_rg_1.user_id = self.user_2
        self.team_1.member_ids = [(3, self.user_2.id)]
        self.region_test_common()

        # SO belong region 2
        so_team_3 = self.sale_order_5.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_3.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_3.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_3.unlink)

    def test_3004_group_sale_regional_manager_parent(self):
        """ user_1 has group_sale_regional_manager
            user_1 is regional manager that region of team_1 is child
            user_1 has all permission in regional that team_1 belongs """

        self.sale_rg_2.user_id = self.user_2
        self.sale_rg_1.parent_id = self.sale_rg_2
        self.team_1.member_ids = [(3, self.user_2.id)]

        self.region_test_common()

        # SO belong region 2
        so_team_3 = self.sale_order_5.with_user(self.user_2)
        so_team_3.read([])
        so_team_3.write({'state': 'cancel'})
        so_team_3.unlink()

    def test_3004_group_sale_regional_manager_child(self):
        """ user_1 has group_sale_regional_manager
            user_1 is regional manager of region 2 that child of team_1's region
            user_1 not have any permission with team_1's records """

        self.sale_rg_2.write({
            'user_id': self.user_2.id,
            'parent_id': self.sale_rg_1.id
            })
        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id,
            'member_ids': [(3, self.user_2.id)]
            })
        self.team_2.crm_team_region_id = self.sale_rg_1

        self.user_1.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_2.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_3.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_team_leader').ids)]
        self.user_4.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]

        # SO created by region manager team 1
        so_team_1 = self.sale_order_1.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_1.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_1.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO created by salesman team 1
        so_team_1 = self.sale_order_3.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_1.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_1.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO without salesperson, team, region
        so_without_user = self.sale_order_4.with_user(self.user_2)
        so_without_user.read([])
        so_without_user.write({'state': 'cancel'})
        so_without_user.unlink()

        # SO created by leader of team belongs region 1
        so_team_2 = self.sale_order_2.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_2.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_2.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_2.unlink)

    def test_3005_group_sale_regional_manager_assistant_direct(self):
        """ user_1 has group_sale_regional_manager
            user_1 is assistant region of region 1
            user_1 has all permission to records belonging region 1"""
        self.sale_rg_1.user_assistant_ids = [self.user_2.id]
        self.region_test_common()

    def test_3006_group_sale_regional_manager_assistant_parent(self):
        """ user_1 has group_sale_regional_manager
            user_1 is assistant region of region 1
            user_1 has all permission to records belonging region 1"""
        self.sale_rg_2.user_assistant_ids = [self.user_2.id]
        self.sale_rg_1.parent_id = self.sale_rg_2
        self.team_1.member_ids = [(3, self.user_2.id)]

        self.region_test_common()

    def test_3007_group_sale_regional_manager_assistant_child(self):
        """ user_1 has group_sale_regional_manager
            user_1 is regional manager of region 2 that child of team_1's region
            user_1 not have any permission with team_1's records """

        self.sale_rg_2.write({
            'user_assistant_ids': [(6, 0, [self.user_2.id])],
            'parent_id': self.sale_rg_1.id
            })

        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id,
            'member_ids': [(3, self.user_2.id)]
            })
        self.team_2.crm_team_region_id = self.sale_rg_1

        self.user_1.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_2.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_regional_manager').ids)]
        self.user_3.groups_id = [(6, 0, self.env.ref('to_sales_team_advanced.group_sale_team_leader').ids)]
        self.user_4.groups_id = [(6, 0, self.env.ref('sales_team.group_sale_salesman').ids)]

        # SO created by region manager team 1
        so_team_1 = self.sale_order_1.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_1.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_1.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO created by salesman team 1
        so_team_1 = self.sale_order_3.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_1.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_1.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_1.unlink)

        # SO without salesperson, team, region
        so_without_user = self.sale_order_4.with_user(self.user_2)
        so_without_user.read([])
        so_without_user.write({'state': 'cancel'})
        so_without_user.unlink()

        # SO created by leader of team belongs region 1
        so_team_2 = self.sale_order_2.with_user(self.user_2)
        self.assertRaises(AccessError, so_team_2.check_access_rule, 'read')
        self.assertRaises(AccessError, so_team_2.write, {'state': 'cancel'})
        self.assertRaises(AccessError, so_team_2.unlink)
