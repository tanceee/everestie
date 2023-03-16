# -*- coding: utf-8 -*-

from datetime import datetime
import pytz
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProductionLot(models.Model):
	_inherit = "stock.production.lot"

	def convert_TZ_UTC(self, TZ_datetime):
		user_tz = self.env.user.tz or pytz.utc
		local = pytz.timezone(user_tz)
		if local:
			time = datetime.strftime(pytz.utc.localize(datetime.strptime(TZ_datetime, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %H:%M:%S")
			return time


	# def name_get(self):
	# 	self.browse(self.ids).read(['name', 'expiration_date'])
	# 	return [(lot.id, '%s%s' % (lot.expiration_date and '[%s] ' % lot.expiration_date or '', lot.name))
    #             for lot in self]

	# def name_get(self):
	# 	res = []
	# 	self.browse(self.ids).read(['name', 'expiration_date'])
	# 	for rec in self:
	# 		expiration_date = False
	# 		if rec.expiration_date:
	# 			expiration_date = self.convert_TZ_UTC(fields.Datetime.to_string(rec.expiration_date))
	# 		res.append((rec.id, '%s - %s' % (rec.name, expiration_date) if rec.expiration_date else rec.name))
	# 	return res