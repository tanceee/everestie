from odoo import api, fields, models, _
import uuid
from datetime import datetime


class FiscalizationHeader(models.Model):
    _name = "fiscalization.header"

    header_UUID = fields.Char(string="Header UUID", readonly=True)
    header_send_datetime = fields.Char("Header Date Time", readonly=True)
    header_subseq_delivery_type = fields.Selection(selection=[('no_internet', 'NOINTERNET'),
                                                              ('bound_book', 'BOUNDBOOK'),
                                                              ('service', 'SERVICE'),
                                                              ('technical_error', 'TECHNICALERROR')], default='service')
    invoice_order_number = fields.Char("Order Number")
    invoice_number = fields.Char("Order Number")

    @api.model
    def create(self, vals):
        res = super(FiscalizationHeader, self).create(vals)
        res['header_UUID'] = uuid.uuid4()
        res['header_send_datetime'] = datetime.now().astimezone().replace(microsecond=0).isoformat()
        res['invoice_order_number'] = self.env['ir.sequence'].next_by_code('pos.order.sequence.number')
        res['invoice_number'] = res['invoice_order_number'] + '/' + str(
            datetime.now().astimezone().replace(microsecond=0).year) + '/' + 'dgh96sf167'
        return res
