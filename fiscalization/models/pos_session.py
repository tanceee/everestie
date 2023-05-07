import base64
import json
import os
import uuid
from datetime import datetime

import requests
from Crypto.Hash import SHA256, MD5
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from OpenSSL import crypto
from dateutil import tz

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from ..services.invoice import make_invoice
from ..services.qr_codes.make_invoice_qr_code import make_invoice_qr_code
from ..services.http_calls.request import make_http_call
from ..services.http_calls.response import parse_response
from ..services.cash_deposit import make_cash_deposit
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    # @api.multi
    # def open_cashbox(self):
    #     self.ensure_one()
    #     context = dict(self._context)
    #     balance_type = context.get('balance') or 'start'
    #     context['bank_statement_id'] = self.cash_register_id.id
    #     context['balance'] = balance_type
    #     context['default_pos_id'] = self.config_id.id
    #
    #     action = {
    #         'name': _('Cash Control'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.bank.statement.cashbox',
    #         'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
    #         'type': 'ir.actions.act_window',
    #         'context': context,
    #         'target': 'new'
    #     }
    #
    #     cashbox_id = None
    #     if balance_type == 'start':
    #         cashbox_id = self.cash_register_id.cashbox_start_id.id
    #     else:
    #         cashbox_id = self.cash_register_id.cashbox_end_id.id
    #     if cashbox_id:
    #         action['res_id'] = cashbox_id
    #
    #     return action

    def action_pos_session_closing_controlsss(self):
        order_ids = None
        for session in self:
            order_ids = session.order_ids.filtered(lambda order: not order.is_fiscalized)
            print("order_ids", session.order_ids)
            if order_ids:
                orders_ref = order_ids.mapped("name")
                super(PosSession, self).action_pos_session_closing_control()
                message = _("Some orders from the session %s is not fiscalized yet! \nOrder Ref.:  %s" % (
                    session.name, ", ".join(orders_ref)))
                return self.env["wizard.message"].genrated_message(message)
                # return {
                #     'warning': {
                #         'title': _('Warning!'),
                #         'message': _("Some orders from the session %s is not fiscalized yet! \nOrder Ref.:  %s" % (
                #             session.name, ", ".join(orders_ref)))
                #     }
                # }
                # raise UserError("Some orders from the session %s is not fiscalized yet! \nOrder Ref.:  %s" % (
                #     session.name, ", ".join(orders_ref)))
            # return True
        if not order_ids:
            return super(PosSession, self).action_pos_session_closing_control()

    def set_cashbox_pos(self, cashbox_value, notes, is_initial_cash):
        print("CASH BOX", cashbox_value, is_initial_cash)
        res = "OK"
        if is_initial_cash:
            res = ""
            vals_dict = {}
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Europe/Tirane')
            vals_dict['change_date_time'] = datetime.utcnow().replace(
                tzinfo=from_zone).astimezone(to_zone).replace(
                microsecond=0).isoformat()
            company_id = self.env.user.company_id

            vals_dict['operation'] = "INITIAL"
            vals_dict['cash_amt'] = str("{:.2f}".format(cashbox_value))
            vals_dict["tcr_code"] = self.config_id.tcr_code
            vals_dict['issuer_nuis'] = company_id.vat

            company_p12_certificate = company_id.p12_certificate
            if company_p12_certificate:
                company_p12_certificate = base64.b64decode(company_p12_certificate)
                certificate_password = company_id.certificate_password.encode('utf-8')

            cash_deposit_xml = make_cash_deposit(vals_dict, company_p12_certificate, certificate_password)
            print("cash_deposit_xml", cash_deposit_xml)
            # url = company_id.fiscalization_endpoint
            # response = make_http_call(cash_deposit_xml, url)
            response_parsed = ''

            try:
                url = company_id.fiscalization_endpoint
                response = make_http_call(cash_deposit_xml, url)
                print("RESPONSE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", response)
                # _logger.info("RESPONSE -----> \n\n%s" % response)
                response_parsed = parse_response(response)
                if response_parsed and not isinstance(response_parsed, dict):
                    print("Transferred")
                    res = "OK"
                    super(PosSession, self).set_cashbox_pos(cashbox_value, notes)

                if isinstance(response_parsed, dict):
                    res = response_parsed['Error']
                    raise exceptions.ValidationError(res)
            except requests.Timeout as e:
                _logger.error("Timeout: %s" % e)
                print("Timeout", e)
            except requests.exceptions.RequestException as e:
                _logger.error("RequestException: %s" % e)
                print("11111111", e)
            except Exception as e:
                _logger.error("\n\n There is some unexpected error, halt and check: %s \n\n" % e)
            finally:
                return json.dumps({"response": res})
        else:
            super(PosSession, self).set_cashbox_pos(cashbox_value, notes)
            return json.dumps({"response": res})
        # response_parsed = parse_response(response)
        # if response_parsed:
        #     if isinstance(response_parsed, dict):
        #         raise exceptions.ValidationError(response_parsed['Error'])
        #     else:
        #         print("Transfered")
        # self['fcdc'] = response_parsed


class WkWizardMessage(models.TransientModel):
    _name = "wizard.message"
    _description = "Message Wizard"

    text = fields.Text(string='Message')

    def genrated_message(self, message, name='Warning'):
        partial_id = self.create([{'text': message}]).id
        return {
            'name': name,
            'view_mode': 'form',
            'view_id': self.env.ref('fiscalization.wizard_message_form').id,
            'view_type': 'form',
            'res_model': 'wizard.message',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }
