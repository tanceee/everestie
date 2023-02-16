from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .test_default_team import TestDefaultTeamCommon


@tagged('post_install', '-at_install')
class TestSalesTeamAdvanced(TestDefaultTeamCommon):

    def test_1000_compute_user_id(self):
        self.assertEqual(self.sale_rg_2.user_id.id, False, 'to_sales_team_advanced: Error _compute_user_id')
        self.sale_rg_2.write({
            'parent_id': self.sale_rg_1.id
        })
        self.assertEqual(self.sale_rg_2.user_id.id, self.user_1.id, 'to_sales_team_advanced: Error _compute_user_id')
        self.sale_rg_2.write({
            'parent_id': False,
            'user_id': self.user_2.id
        })
        self.sale_rg_2.write({
            'parent_id': self.sale_rg_1.id
        })
        self.assertEqual(self.sale_rg_2.user_id.id, self.user_2.id, 'to_sales_team_advanced: Error _compute_user_id')

    def test_1001_compute_recursive_child_ids(self):
        self.sale_rg_2.write({
            'parent_id': self.sale_rg_1.id
        })
        self.assertEqual(self.sale_rg_2.id in self.sale_rg_1.recursive_child_ids.ids, True, 'to_sales_team_advanced: Error _compute_recursive_child_ids')

    def test_1002_compute_member_ids(self):
        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id
        })
        self.team_2.write({
            'crm_team_region_id': self.sale_rg_1.id
        })
        self.team_3.write({
            'crm_team_region_id': self.sale_rg_2.id
        })
        self.user_1.write({
            'sale_team_id': self.team_1.id
        })
        self.team_1.write({
            'member_ids': [(3, self.user_2.id)]
            })
        self.user_2.write({
            'sale_team_id': self.team_2.id
        })
        self.team_2.write({
            'member_ids': [(3, self.user_3.id), (4, self.user_2.id)]
            })
        self.user_3.write({
            'sale_team_id': self.team_3.id
        })
        self.team_3.write({
            'member_ids': (4, self.user_3.id)
            })
        self.sale_rg_2.write({
            'parent_id': self.sale_rg_1.id
        })
        self.assertEqual(self.user_1.id in self.sale_rg_1.member_ids.ids, True, 'to_sales_team_advanced: Error _compute_member_ids')
        self.assertEqual(self.user_2.id in self.sale_rg_1.member_ids.ids, True, 'to_sales_team_advanced: Error _compute_member_ids')
        self.assertEqual(self.user_3.id in self.sale_rg_1.member_ids.ids, False, 'to_sales_team_advanced: Error _compute_member_ids')
        self.assertEqual(self.user_1.id in self.sale_rg_2.member_ids.ids, False, 'to_sales_team_advanced: Error _compute_member_ids')
        self.assertEqual(self.user_2.id in self.sale_rg_2.member_ids.ids, False, 'to_sales_team_advanced: Error _compute_member_ids')
        self.assertEqual(self.user_3.id in self.sale_rg_2.member_ids.ids, True, 'to_sales_team_advanced: Error _compute_member_ids')

    def test_1003_group_sale_salesman(self):
        """ user has group group_sale_salesman
            user_1 can only read team_1"""
        group_sale_salesman = self.env.ref('sales_team.group_sale_salesman').id
        self.user_1.write({
            'groups_id': [(6, 0, [group_sale_salesman])],
        })
        self.team_1.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).read, ['id'])
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.CrmTeam.with_user(self.user_1).create, {'name': 'test_2'})

        self.sale_rg_1.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).unlink)

        self.sale_rg_2.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.CRMregion.with_user(self.user_1).create, {'name': 'test_2'})

    def test_1004_group_sale_salesman_team_lead(self):
        """ user has group group_sale_salesman and is team leader of team_1
            not change permission"""
        self.team_1.write({
            'user_id': self.user_1.id
        })
        self.test_1003_group_sale_salesman()

    def test_1005_group_sale_salesman_sale_rg(self):
        """ user has group group_sale_salesman and is manager of sale_rg_1
            not change permission"""
        self.sale_rg_1.write({
            'user_id': self.user_1.id
        })
        self.test_1003_group_sale_salesman()

    def test_1006_group_sale_team_leader(self):
        """ user_1 has group_sale_team_leader and is team leader of team_1
            user_1 can read team_1
            user_1 can't read another team
            user_1 can't create a team"""
        group_sale_team_leader = self.env.ref('to_sales_team_advanced.group_sale_team_leader').id
        self.user_1.write({
            'groups_id': [(6, 0, [group_sale_team_leader])],
        })
        self.team_1.write({
            'user_id': self.user_1.id
        })
        self.team_2.write({
            'user_id': self.user_3.id
        })

        self.team_1.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).write, {'member_ids': [(6, 0, [])]})
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).read, ['id'])
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.CrmTeam.with_user(self.user_1).create, {'name': 'test_2'})

        self.sale_rg_1.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).unlink)

        self.sale_rg_2.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.CRMregion.with_user(self.user_1).create, {'name': 'test_2'})

    def test_1007_group_sale_team_leader_sale_rg(self):
        """ user_1 has group_sale_team_leader and is team leader of team_1 and is Manager of sale_rg_1
            not change permission"""
        self.sale_rg_1.write({
            'user_id': self.user_1.id
        })
        self.test_1006_group_sale_team_leader()

    def test_1008_group_sale_regional_manager(self):
        """ user_1 has group_sale_regional_manager and is manager of sale_rg_1
            user_1 can read, write, create all team that it manages"""
        group_sale_regional_manager = self.env.ref('to_sales_team_advanced.group_sale_regional_manager').id
        self.user_1.write({
            'groups_id': [(6, 0, [group_sale_regional_manager])],
        })
        self.sale_rg_1.write({
            'user_id': self.user_1.id,
            'team_ids': [(6, 0, [self.team_1.id])]
        })
        self.sale_rg_2.write({
            'user_id': self.user_3.id,
            'team_ids': [(6, 0, [self.team_2.id])]
        })
        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id
        })
        self.team_2.write({
            'crm_team_region_id': self.sale_rg_2.id,
            'user_id': self.user_3.id
        })
        self.team_1.with_user(self.user_1).read(['id'])
        self.team_1.with_user(self.user_1).write({'name': 'test'})
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).read, ['id'])
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).unlink)

        self.CrmTeam.with_user(self.user_1).create({'name': 'test_2'})

        self.sale_rg_1.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).unlink)

        self.sale_rg_2.with_user(self.user_1).read(['id'])
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).write, {'name': 'test'})
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).unlink)

        self.assertRaises(AccessError, self.CRMregion.with_user(self.user_1).create, {'name': 'test_2'})

    def test_1009_group_sale_regional_manager_team_leader(self):
        self.team_1.write({
            'user_id': self.user_1.id
        })
        self.test_1008_group_sale_regional_manager()

    def test_1010_group_sale_regional_manager_child(self):
        """ sale_rg_1 is parent of sale_rg_2
            user_1 is manager, user_1 can read, write, create all team of sale_rg_2"""
        group_sale_regional_manager = self.env.ref('to_sales_team_advanced.group_sale_regional_manager').id
        self.user_1.write({
            'groups_id': [(6, 0, [group_sale_regional_manager])],
        })
        self.sale_rg_1.write({
            'user_id': self.user_1.id
        })
        self.sale_rg_2.write({
            'parent_id': self.sale_rg_1.id,
            'user_id': self.user_3.id
        })
        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id,
            'member_ids': [(6, 0, [])]
        })
        self.team_2.write({
            'crm_team_region_id': self.sale_rg_2.id,
            'user_id': self.user_3.id,
            'member_ids': [(6, 0, [])]
        })

        self.team_2.with_user(self.user_1).read(['id'])
        self.team_2.with_user(self.user_1).write({'name': 'test'})
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).unlink)

    def test_1011_group_sale_salesman_all_leads(self):
        """ user_1 has group_sale_salesman_all_leads
            user_1 can read, write, create all team
            user_1 only has not delete permission"""
        group_sale_salesman_all_leads = self.env.ref('sales_team.group_sale_salesman_all_leads').id
        self.user_1.write({
            'groups_id': [(6, 0, [group_sale_salesman_all_leads])],
        })
        self.sale_rg_1.write({
            'user_id': self.user_1.id,
            'team_ids': [(6, 0, [self.team_1.id])]
        })
        self.sale_rg_2.write({
            'user_id': self.user_3.id,
            'team_ids': [(6, 0, [self.team_2.id])]
        })
        self.team_1.write({
            'crm_team_region_id': self.sale_rg_1.id
        })
        self.team_2.write({
            'crm_team_region_id': self.sale_rg_2.id,
            'user_id': self.user_3.id
        })
        self.team_1.with_user(self.user_1).read(['id'])
        self.team_1.with_user(self.user_1).write({'name': 'test'})
        self.assertRaises(AccessError, self.team_1.with_user(self.user_1).unlink)

        self.team_2.with_user(self.user_1).read, ['id']
        self.team_2.with_user(self.user_1).write, {'name': 'test'}
        self.assertRaises(AccessError, self.team_2.with_user(self.user_1).unlink)

        self.CrmTeam.with_user(self.user_1).create({'name': 'test_2'})

        self.sale_rg_1.with_user(self.user_1).read(['id'])
        self.sale_rg_1.with_user(self.user_1).write, {'name': 'test'}
        self.assertRaises(AccessError, self.sale_rg_1.with_user(self.user_1).unlink)

        self.sale_rg_2.with_user(self.user_1).read(['id'])
        self.sale_rg_2.with_user(self.user_1).write, {'name': 'test'}
        self.assertRaises(AccessError, self.sale_rg_2.with_user(self.user_1).unlink)

        self.CRMregion.with_user(self.user_1).create, {'name': 'test_2'}
