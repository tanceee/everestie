# -*- coding: utf-8 -*-

from datetime import datetime
import pytz
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class ProductionLot(models.Model):
	_inherit = "stock.production.lot"

	# @api.model
	# def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
	# 	fields.append('expiration_date')
	# 	result = super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
	# 	for lot in result:
	# 		lot['name'] = '%s-%s' %(lot.get('name'), lot.get('expiration_date'))
	# 	return result

	# def convert_TZ_UTC(self, TZ_datetime):
	# 	user_tz = self.env.user.tz or pytz.utc
	# 	local = pytz.timezone(user_tz)
	# 	if local:
	# 		time = datetime.strftime(pytz.utc.localize(datetime.strptime(TZ_datetime, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %H:%M:%S")
	# 		return time

	# def name_get(self):
	# 	res = []
	# 	self.browse(self.ids).read(['name', 'expiration_date'])
	# 	for rec in self:
	# 		expiration_date = False
	# 		if rec.expiration_date:
	# 			expiration_date = self.convert_TZ_UTC(fields.Datetime.to_string(rec.expiration_date))
	# 		res.append((rec.id, '%s - %s' % (rec.name, expiration_date) if rec.expiration_date else rec.name))
	# 	return res

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"


	lot_id = fields.Many2one("stock.production.lot", "Lot", copy=False)
	expiration_date = fields.Datetime(copy=False)

	@api.onchange("product_id")
	def product_id_change(self):
		res = super().product_id_change()
		self.lot_id = False
		return res

	# @api.onchange("lot_id")
	# def lot_id_onchange(self):
	# 	if self.lot_id:
	# 		self.expiration_date = self.lot_id.expiration_date

	@api.onchange("product_id")
	def _onchange_product_id_set_lot_domain(self):
		available_lot_ids = []
		if self.order_id.warehouse_id and self.product_id:
			location = self.order_id.warehouse_id.lot_stock_id
			quants = self.env["stock.quant"].read_group(
				[
					("product_id", "=", self.product_id.id),
					("location_id", "child_of", location.id),
					("quantity", ">", 0),
					("lot_id", "!=", False),
				],
				["lot_id"],
				"lot_id",
			)
			available_lot_ids = [quant["lot_id"][0] for quant in quants]
		self.lot_id = False
		return {"domain": {"lot_id": [("id", "in", available_lot_ids)]}}

class StockMove(models.Model):
	_inherit = "stock.move"

	def _update_reserved_quantity(self,need,available_quantity,location_id,lot_id=None,package_id=None,owner_id=None,strict=True,):
		if self.sale_line_id.lot_id:
			lot_id = self.sale_line_id.lot_id
		return super()._update_reserved_quantity(need,available_quantity,location_id,lot_id=lot_id,package_id=package_id,owner_id=owner_id,strict=strict)

	def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
		vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
		if reserved_quant and self.sale_line_id.lot_id:
			vals.update({"lot_id" : self.sale_line_id.lot_id.id, 'expiration_date' : self.sale_line_id.lot_id.expiration_date})
		return vals
