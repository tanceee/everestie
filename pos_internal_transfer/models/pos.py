# -*- coding: utf-8 -*-

from odoo import fields, models,tools,api
import logging


class pos_config(models.Model):
	_inherit = 'pos.config'

	allow_internal_transfer = fields.Boolean('Allow Internal Transfer')
	allow_internal_locations = fields.Many2many("stock.location","stock_config_loaction","stock_location","config_location","Internal Locations",domain="[('usage', '=', 'internal'),('company_id','=',company_id)]")
	allow_picking_type_ids = fields.Many2many("stock.picking.type","stock_picking_type_config_id","config_id","stock_type_id","Picking Type",domain="[('code', '=', 'internal'),('warehouse_id.company_id','=',company_id)]")


class PosOrderInherit(models.Model):
	_inherit = 'pos.session'


	@api.model
	def create_stock_picking(self,client,picking_type,src,dest,state,product,company_id):
		# print("Testing>>>>>>>>>>>>>>>>>>>>>",client,picking_type,src,dest,state,product)
		pick = self.env['stock.picking'].create({
				'company_id': company_id,
				'partner_id': client or False,
				'location_id': int(src),
				'location_dest_id': int(dest),
				'picking_type_id': int(picking_type),
				})
		if pick.picking_type_id:
			pick.operating_unit_id = pick.picking_type_id.warehouse_id.operating_unit_id.id
		for i in product:
			product_obj = self.env['product.product'].search([('id','=',i.get('product_id')),('type','in',['consu','product'])])
			if product_obj:
				res = self.env['stock.move'].create({
										'product_id' : product_obj.id,
										'name':product_obj.name,
										'product_uom_qty' :i.get('quantity'),
										'picking_id':pick.id,
										'location_id':pick.location_id.id,
										'location_dest_id':pick.location_dest_id.id,
										'product_uom':product_obj.uom_id.id,
										'picking_type_id' :int(picking_type)
										})			
		if state=='waiting':
			pick.action_confirm()
		
		if state=="done":
			pick.action_confirm()
			pick.force_assign()
			for j in pick.pack_operation_product_ids:
				stock_operation_obj = self.env['stock.pack.operation'].browse(j.id)
				for i in product:
					product_obj = self.env['product.product'].search([('id','=',i.get('product_id')),('type','in',['consu','product'])])
					if product_obj:
						if stock_operation_obj.product_id.id == i.get('product_id'):
							res = j.write({'qty_done': i.get('quantity')})
			pick.do_new_transfer()

		return pick.name 
		

