from odoo.tests import tagged

from .test_default_team import TestDefaultTeamCommon


@tagged('post_install', '-at_install')
class TestRegionsHierarchy(TestDefaultTeamCommon):

    def test_2010_regions_hierarchy(self):
        # # SETUP hierarchy: sale_rg_3 -> sale_rg_2 -> sale_rg_1
        self.sale_rg_3.write({'parent_id': self.sale_rg_2.id})
        self.sale_rg_2.write({'parent_id': self.sale_rg_1.id})
        # check child relationship
        self.assertEqual(self.sale_rg_1.child_ids.ids, self.sale_rg_2.ids)
        self.assertEqual(self.sale_rg_1.recursive_child_ids.ids, [self.sale_rg_2.id, self.sale_rg_3.id])
        self.assertEqual(self.sale_rg_2.child_ids.ids, self.sale_rg_3.ids)
        self.assertEqual(self.sale_rg_2.recursive_child_ids.ids, [self.sale_rg_3.id])
        # check parent relationship
        self.assertEqual(self.sale_rg_1.recursive_parent_ids.ids, [])
        self.assertEqual(self.sale_rg_2.recursive_parent_ids.ids, [self.sale_rg_1.id])
        self.assertEqual(self.sale_rg_3.recursive_parent_ids.ids, [self.sale_rg_2.id, self.sale_rg_1.id])

        # # BREAK the chain to say: sale_rg_3 -> sale_rg_2 | sale_rg_1
        self.sale_rg_2.write({'parent_id': False})
        # check child relationship
        self.assertEqual(self.sale_rg_1.child_ids.ids, [])
        self.assertEqual(self.sale_rg_1.recursive_child_ids.ids, [])
        self.assertEqual(self.sale_rg_2.child_ids.ids, self.sale_rg_3.ids)
        self.assertEqual(self.sale_rg_2.recursive_child_ids.ids, [self.sale_rg_3.id])
        # check parent relationship
        self.assertEqual(self.sale_rg_1.recursive_parent_ids.ids, [])
        self.assertEqual(self.sale_rg_2.recursive_parent_ids.ids, [])
        self.assertEqual(self.sale_rg_3.recursive_parent_ids.ids, [self.sale_rg_2.id])
