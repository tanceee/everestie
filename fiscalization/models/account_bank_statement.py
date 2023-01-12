import datetime
import uuid

from dateutil import tz
from odoo import api, fields, models, _, exceptions
from ..services.cash_deposit import make_cash_deposit
from ..services.http_calls.response import parse_response
from ..services.http_calls.request import make_http_call
import base64


class FiscalizationCashDeposit(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    def _get_default_pos_cofig(self):
        if self._context.get('active_id'):
            session_id = self.env['pos.session'].browse(int(self._context.get('active_id')))
            return session_id.config_id.id
        else:
            return False

    operation = fields.Selection([('INITIAL', 'INITIAL'), ('WITHDRAW', 'WITHDRAW'), ('DEPOSIT', 'DEPOSIT')],
                                 default='INITIAL')
    fcdc = fields.Char('Kodi unik i depozites fillestare i sjell nga tatimet', default=None)
    direct_amount_input = fields.Boolean(default=True)
    direct_amount = fields.Float()
    pos_config_id = fields.Many2one('pos.config', default=_get_default_pos_cofig)
    is_initial_cash = fields.Boolean(default=True)

    @api.onchange("direct_amount_input", "direct_amount")
    def set_amount_direct(self):
        if self.direct_amount_input and self.direct_amount:
            self.cashbox_lines_ids = False
            self.cashbox_lines_ids = [(0, 0, {'coin_value': self.direct_amount, 'number': 1})]
        else:
            self.direct_amount = 0

    def validate(self):
        res = super(FiscalizationCashDeposit, self).validate()
        return res

    @api.model
    def create(self, vals):
        res = super(FiscalizationCashDeposit, self).create(vals)
        vals_dict = {}
        context = dict(self._context)
        balance_type = context.get('balance') or 'start'
        print("1111111111", balance_type)
        if balance_type == 'start' and res.is_initial_cash:
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Europe/Tirane')
            vals_dict['change_date_time'] = datetime.datetime.utcnow().replace(
                tzinfo=from_zone).astimezone(to_zone).replace(
                microsecond=0).isoformat()
            company_id = self.env.user.company_id
            line_id = self.env['account.cashbox.line'].search([('cashbox_id', '=', res.id)], limit=1)
            # tcr_code = 'vc813ms173'
            # if line_id and line_id.default_pos_id:
            #     tcr_code = line_id.default_pos_id.tcr_code
            vals_dict['operation'] = getattr(vals_dict, 'operation', 'INITIAL')
            vals_dict['cash_amt'] = str(
                "{:.2f}".format(sum([el['coin_value'] * el['number'] for el in res['cashbox_lines_ids']])))
            vals_dict["tcr_code"] = res.pos_config_id.tcr_code
            vals_dict['issuer_nuis'] = company_id.vat

            company_p12_certificate = company_id.p12_certificate.datas
            certificate_password = ""
            if company_p12_certificate:
                company_p12_certificate = base64.b64decode(company_p12_certificate)
                certificate_password = company_id.certificate_password.encode('utf-8')

            cash_deposit_xml = make_cash_deposit(vals_dict, company_p12_certificate=company_p12_certificate,
                                                 certificate_password=certificate_password)

            url = company_id.fiscalization_endpoint
            response = make_http_call(cash_deposit_xml, url)
            response_parsed = parse_response(response)
            if response_parsed:
                if isinstance(response_parsed, dict):
                    raise exceptions.ValidationError(response_parsed['Error'])
                else:
                    res['fcdc'] = response_parsed
            print("!111111111111", response_parsed)
        return res

    # @api.multi
    # def write(self, vals):
    #     self.ensure_one()
    #     res = super(FiscalizationCashDeposit, self).create(vals)
    #     return res
