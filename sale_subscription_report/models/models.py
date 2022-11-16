# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import calendar


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def add_months(self, source_date, months):
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day).strftime("%b, %Y")
