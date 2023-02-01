# -*- coding: utf-8 -*-
import requests
from odoo.addons.point_of_sale.wizard.pos_box import PosBox
import datetime
import uuid
import base64

from dateutil import tz
from odoo import api, fields, models, _, exceptions
from ..services.cash_deposit import make_cash_deposit
from ..services.http_calls.response import parse_response
from ..services.http_calls.request import make_http_call
import logging

_logger = logging.getLogger(__name__)


# class PosBoxIn2(PosBox):
#     _inherit = 'cash.box.out'
#
#     def _get_default_pos_cofig(self):
#         if self._context.get('active_id'):
#             session_id = self.env['pos.session'].browse(int(self._context.get('active_id')))
#             return session_id.config_id.id
#         else:
#             return False
#
#     pos_config_id = fields.Many2one('pos.config',default=_get_default_pos_cofig)
#
#     def run(self):
#         res = super(PosBoxIn2, self).run()
#         vals_dict = {}
#
#         from_zone = tz.gettz('UTC')
#         to_zone = tz.gettz('Europe/Tirane')
#         vals_dict['change_date_time'] = datetime.datetime.utcnow().replace(
#             tzinfo=from_zone).astimezone(to_zone).replace(
#             microsecond=0).isoformat()
#         company_id = self.env.user.company_id
#
#         vals_dict['operation'] = getattr(vals_dict, 'operation', 'DEPOSIT')
#         vals_dict['cash_amt'] = str("{:.2f}".format(self.amount))
#         vals_dict["tcr_code"] = self.pos_config_id.tcr_code
#         vals_dict['issuer_nuis'] = company_id.vat
#
#         company_p12_certificate = company_id.p12_certificate.datas
#         if company_p12_certificate:
#             company_p12_certificate = base64.b64decode(company_p12_certificate)
#             certificate_password = company_id.certificate_password.encode('utf-8')
#
#         cash_deposit_xml = make_cash_deposit(vals_dict,company_p12_certificate,certificate_password)
#         url = company_id.fiscalization_endpoint
#         response = make_http_call(cash_deposit_xml,url)
#         response_parsed = parse_response(response)
#         if response_parsed:
#             if isinstance(response_parsed, dict):
#                 raise exceptions.ValidationError(response_parsed['Error'])
#             else:
#                 print("Transfered")
#                 # self['fcdc'] = response_parsed
#         return res

class PosBoxOut(PosBox):
    _inherit = 'cash.box.out'

    def _get_default_pos_cofig(self):
        if self._context.get('active_id'):
            session_id = self.env['pos.session'].browse(int(self._context.get('active_id')))
            return session_id.config_id.id
        else:
            return False

    pos_config_id = fields.Many2one('pos.config', default=_get_default_pos_cofig)

    # def run(self):
    #     res = super(PosBoxOut2, self).run()
    #     vals_dict = {}
    #
    #     from_zone = tz.gettz('UTC')
    #     to_zone = tz.gettz('Europe/Tirane')
    #     vals_dict['change_date_time'] = datetime.datetime.utcnow().replace(
    #         tzinfo=from_zone).astimezone(to_zone).replace(
    #         microsecond=0).isoformat()
    #     company_id = self.env.user.company_id
    #
    #     vals_dict['operation'] = getattr(vals_dict, 'operation', 'WITHDRAW')
    #     vals_dict['cash_amt'] = str("{:.2f}".format(self.amount))
    #     vals_dict["tcr_code"] = self.pos_config_id.tcr_code
    #     vals_dict['issuer_nuis'] = company_id.vat
    #
    #     company_id = self.env.user.company_id
    #     company_p12_certificate = company_id.p12_certificate.datas
    #     if company_p12_certificate:
    #         company_p12_certificate = base64.b64decode(company_p12_certificate)
    #         certificate_password = company_id.certificate_password.encode('utf-8')
    #
    #     cash_deposit_xml = make_cash_deposit(vals_dict,company_p12_certificate,certificate_password)
    #     url = company_id.fiscalization_endpoint
    #     response = make_http_call(cash_deposit_xml,url)
    #     response_parsed = parse_response(response)
    #     if response_parsed:
    #         if isinstance(response_parsed, dict):
    #             raise exceptions.ValidationError(response_parsed['Error'])
    #         else:
    #             print("Transfered")
    #             # self['fcdc'] = response_parsed
    #     return res

    def run(self):
        result = super(PosBoxOut, self).run()
        vals_dict = {}
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Tirane')
        vals_dict['change_date_time'] = datetime.datetime.utcnow().replace(
            tzinfo=from_zone).astimezone(to_zone).replace(
            microsecond=0).isoformat()
        company_id = self.env.user.company_id
        if self.amount < 0:
            operation = "WITHDRAW"
            amount = self.amount * -1
        else:
            operation = "DEPOSIT"
            amount = self.amount
        active_ids = self._context.get("active_ids")
        session_id = self.env["pos.session"].browse(active_ids)
        vals_dict['operation'] = operation
        vals_dict['cash_amt'] = str("{:.2f}".format(amount))
        vals_dict["tcr_code"] = session_id.config_id.tcr_code
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

        except requests.Timeout as e:
            _logger.error("Timeout: %s" % e)
            print("Timeout", e)
        except requests.exceptions.RequestException as e:
            _logger.error("RequestException: %s" % e)
            print("11111111", e)
        except Exception as e:
            _logger.error("\n\n There is some unexpected error, halt and check: %s \n\n" % e)
        if response_parsed and not isinstance(response_parsed, dict):
            print("Transferred")
            # res = "OK"
        if isinstance(response_parsed, dict):
            res = response_parsed['Error']
            raise exceptions.ValidationError(res)
        return result
