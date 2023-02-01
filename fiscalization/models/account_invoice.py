from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    from_pos = fields.Boolean(compute="_compute_inv_from_pos")
    qrcode_from_pos = fields.Binary(compute="_compute_inv_from_pos")
    iic_from_pos = fields.Char(compute="_compute_inv_from_pos")
    fic_from_pos = fields.Char(compute="_compute_inv_from_pos")
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")
    transporter_id = fields.Many2one("res.partner")
    license_plate_no = fields.Char()
    delivery_datetime = fields.Datetime()

    def _compute_inv_from_pos(self):
        for rec in self:
            pos_invoice_id = self.env['pos.order'].search([('account_move', '=', rec.id)])
            if pos_invoice_id:
                rec.from_pos = True
                rec.qrcode_from_pos = pos_invoice_id.qr_code
                rec.iic_from_pos = pos_invoice_id.iic_code
                rec.fic_from_pos = pos_invoice_id.fic
                rec.operating_unit_id = pos_invoice_id.operating_unit_id.id
            else:
                rec.from_pos = False
                rec.qrcode_from_pos = False
                rec.iic_from_pos = False
                rec.fic_from_pos = False
