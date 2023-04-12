from odoo import api, fields, models, tools


class PosOrder(models.Model):
    _inherit = "pos.order"
    _auto = False

    attendee_id = fields.Many2one(comodel_name='event.registration', string='Registration')
    question_id = fields.Many2one(comodel_name='event.question', string='Question')
    answer_id = fields.Many2one(comodel_name='event.answer', string='Answer')
    event_id = fields.Many2one(comodel_name='event.event', string='Event')

    @api.model_cr
    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'event_question_report')
        self._cr.execute(""" CREATE VIEW event_question_report AS (
            SELECT
                att_answer.id as id,
                att_answer.event_registration_id as attendee_id,
                answer.question_id as question_id,
                answer.id as answer_id,
                question.event_id as event_id
            FROM
                event_registration_answer as att_answer
            LEFT JOIN
                event_answer as answer ON answer.id = att_answer.event_answer_id
            LEFT JOIN
                event_question as question ON question.id = answer.question_id
            GROUP BY
                attendee_id,
                event_id,
                question_id,
                answer_id,
                att_answer.id
        )""")


class SaleProductsByCustomer(models.Model):
    _name = "sale.order.product"
    _auto = False

    partner_id = fields.Many2one('res.partner')
    orders = fields.Integer(string='Total Orders')
    name = fields.Char(string='Name')
    price_total = fields.Float(string='Total Payment')
    qty = fields.Integer(string='Qty Ordered')
    last_order = fields.Date(string='Last Order Date')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'sale_order_product')
        tools.drop_view_if_exists(self._cr, 'sale_order_product_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW sale_order_product_report AS (
                SELECT so.order_partner_id AS id, count(so.id) AS orders, pt.name, sum(so.price_total) AS price_total,
                    sum(so.product_uom_qty) AS qty, max(so.create_date) AS last_order
                FROM public.sale_order_line AS so
                LEFT JOIN public.product_product AS pr ON so.product_id = pr.id
                LEFT JOIN public.product_template AS pt ON pr.product_tmpl_id = pt.id
                GROUP BY so.order_partner_id, so.product_id, pt.name
                ORDER BY qty DESC
            )""")
