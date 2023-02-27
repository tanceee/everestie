from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    is_reverse_charge = fields.Selection(string="A paguhet TVSH nga bleresi?", selection=[('true', 'true'), ('false', 'false')],
                                    default='false')


class AttachDocLink(models.Model):
    _name = "attach.doc.link"

    name = fields.Char()
    link = fields.Char()
    invoice_id = fields.Many2one("account.move")
