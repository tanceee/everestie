# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProductionLot(models.Model):
	_inherit = "stock.production.lot"

	def name_get(self):
		res = []
		for rec in self:
			res.append((rec.id, '%s - %s' % (rec.name, rec.expiration_date) if rec.expiration_date else rec.name))
		return res