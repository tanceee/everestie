# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import datetime

class PosConfig(models.Model):
	_inherit = 'pos.config'

	location_id = fields.Many2one(related='picking_type_id.default_location_src_id')

class StockQuant(models.Model):
	_inherit = 'stock.quant'

	reserve_quant = fields.Float('Reserved')
	expiration_date = fields.Datetime(related="lot_id.expiration_date", store=True)
	is_expired = fields.Boolean(compute='_compute_is_expired')

	def _compute_is_expired(self):
		for rec in self:
			if rec.expiration_date and rec.expiration_date > datetime.datetime.now():
				rec.is_expired = False
			elif not rec.expiration_date:
				rec.is_expired = False
			else:
				rec.is_expired = True

	@api.model
	def update_stock_quantity(self, prd, line):
		rec = self.browse(prd['id'])
		rec.reserve_quant += line
		return {}

	def convert_in_timzone(self, date_to_convert):
		user_tz = self.env.user.tz or pytz.utc
		local = pytz.timezone(user_tz)
		if local:
			time = datetime.strftime(pytz.utc.localize(datetime.strptime(date_to_convert, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %H:%M:%S")
			return time