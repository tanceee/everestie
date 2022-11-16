# -*- coding: utf-8 -*-

from odoo import fields, models, _,api
from odoo.exceptions import UserError
import xlwt
from xlwt import *
import base64
from io import BytesIO
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountPartnerLedger(models.TransientModel):
    _name = "account.common.report.wiz"
    _descreption = 'Pl Report Wizard'
    
    @api.model
    def _default_pl_partner_ids(self):
        if self._context.get('partner_pl', False):
            return [(6, 0, self._context.get('active_ids', False))]
    
    currency_id = fields.Many2one('res.currency', 'Currency')
    with_initial =fields.Boolean('With Initial Balance',default=True)
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                        ('supplier', 'Payable Accounts'),
                                        ('customer_supplier', 'Receivable and Payable Accounts')
                                      ], string="Partner's", required=True, default='customer')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    pl_partner_ids = fields.Many2many('res.partner', 'pl_partner_ids_rel', 'pl_common_idd', 'partner_id', string='Partners ', default=_default_pl_partner_ids)
    
    
    def print_report_fc(self):
        data = self[0].read()
        if self.pl_partner_ids:
            data[0].update({'active_ids': self.pl_partner_ids.ids})
        else:
            data[0].update({'active_ids': self.pl_partner_ids.search([]).ids})
        return self.env.ref('pl_foreign_currency.action_report_partnerledger').report_action(self, data={'form':data[0]})
    
    @api.model
    def format_value(self, amount, currency=False, blank_if_zero=False):
        ''' Format amount to have a monetary display (with a currency symbol).
        E.g: 1000 => 1000.0 $

        :param amount:          A number.
        :param currency:        An optional res.currency record.
        :param blank_if_zero:   An optional flag forcing the string to be empty if amount is zero.
        :return:                The formatted amount as a string.
        '''
        currency_id = currency or self.env.company.currency_id
        amount = amount

        if self.env.context.get('no_format'):
            return amount
        return formatLang(self.env, amount, currency_obj=currency_id)
    
    def export_excel_fc(self):
        company_currency = self.env.company.currency_id
        data = self[0].read()
        if 'active_ids' in self._context:
            data[0].update({'active_ids':self._context['active_ids']})
        if self.pl_partner_ids:
            partner_ids = self.pl_partner_ids
        else:
            partner_ids = self.pl_partner_ids.search([])
        
        header_style = 'font: name Arial ; font:height 300; align: wrap on, vert center, horiz center'
        header_style1 = 'font: name Arial , bold on; font:height 225'
        number_style = 'align: wrap on, horiz right'
        number_style1 = 'align: wrap on, horiz right'
        
        report = xlwt.Workbook()
        sheet = report.add_sheet("Partner Ledger", cell_overwrite_ok=True)
        sheet.write_merge(1,2 ,4 ,6 , "Partner Ledger", Style.easyxf(header_style))
        
        partners = ''
        for part in partner_ids:
            partners += part.name+','
        partners = partners[:-1]
        x = 4
        first = True
        for partner in partner_ids:
            sheet.write(x, 0 , 'Company:', Style.easyxf(header_style1))
            sheet.write(x+1, 0 , self.env.company.name)
            sheet.write(x, 3 , 'Partner:', Style.easyxf(header_style1))
            sheet.write(x+1, 3 , partner.name)
            sheet.write(x, 5 , 'Target Moves:', Style.easyxf(header_style1))
            sheet.write(x+1, 5 , 'All Entries' if self.target_move == 'all' else 'All Posted Entries')
            if self.date_from:
                sheet.write(x, 7 , 'Date From:', Style.easyxf(header_style1))
                sheet.write(x+1, 7 , self.date_from)
            if self.date_to:
                sheet.write(x, 9 , 'Date To:', Style.easyxf(header_style1))
                sheet.write(x+1, 9 , self.date_to)
                
            x += 3
            sheet.write(x, 0 , 'Date', Style.easyxf(header_style1))
            sheet.write(x, 1 , 'JRNL', Style.easyxf(header_style1))
            sheet.write(x, 2 , 'Ref', Style.easyxf(header_style1))
            sheet.write(x, 3 , 'Debit', Style.easyxf(header_style1))
            sheet.write(x, 4 , 'Credit', Style.easyxf(header_style1))
            sheet.write(x, 5 , 'Balance', Style.easyxf(header_style1))
            sheet.write(x, 6 , 'Balance in BC', Style.easyxf(header_style1))
            x += 1
        
            datas = self.env['report.pl_foreign_currency.partnerledger'].get_lines({'form':data[0]},partner)
            for line in datas:
                sheet.write_merge(x, x, 0, 2 , line['cu'].name,Style.easyxf(header_style1))
                x += 1  
                bal = 0.0
                bal_bc = 0.0
                tot_debit = 0.0
                tot_credit = 0.0
                tot_debit_bc = 0.0
                tot_credit_bc = 0.0
                tot_cur = False
                
                if self.with_initial:
                    sheet.write(x, 2 , 'Initial Balance')
                    sheet.write(x, 3 , self.format_value(line['bal']['debit'], line['cu']))
                    sheet.write(x, 4 , self.format_value(line['bal']['credit'], line['cu']))
                    sheet.write(x, 5 , self.format_value(line['bal']['debit'] - line['bal']['credit'], line['cu']) )
                    sheet.write(x, 6 , self.format_value(line['bal']['debit_bc'] - line['bal']['credit_bc'], company_currency) )
                    x += 1
                    
                    tot_credit += line['bal']['credit']
                    tot_debit += line['bal']['debit']
                    tot_credit_bc += line['bal']['credit_bc']
                    tot_debit_bc += line['bal']['debit_bc']
                    bal = line['bal']['debit']-line['bal']['credit']+bal
                    bal_bc = line['bal']['debit_bc']-line['bal']['credit_bc']+bal_bc
                    
                for l in line['lines']:
                    if l['date']:
                        bal = l['debit']-l['credit']+bal
                        bal_bc = l['debit_bc']-l['credit_bc']+bal_bc
                        jname = l['jname']
                        if l['ref']:
                            jname+= '-'+l['ref']
                        if l['name']:
                            jname+= '-'+l['name']
                        sheet.write(x, 0 , str(l['date'].strftime(get_lang(self.env).date_format)))
                        sheet.write(x, 1 , l['code'])
                        sheet.write(x, 2 , jname)
                        sheet.write(x, 3 , self.format_value(l['debit'], l['currency_id']))
                        sheet.write(x, 4 , self.format_value(l['credit'], l['currency_id']))
                        sheet.write(x, 5 , self.format_value(bal, l['currency_id']))
                        sheet.write(x, 6 , self.format_value(bal_bc, company_currency))
                        x+=1
                        tot_credit += l['credit']
                        tot_debit += l['debit']
                        tot_credit_bc += l['credit_bc']
                        tot_debit_bc += l['debit_bc']
                        tot_cur = l['currency_id']
                sheet.write(x+2,2,'Total', Style.easyxf(header_style1))
                sheet.write(x+2,3,self.format_value(tot_debit, tot_cur), Style.easyxf(header_style1))
                sheet.write(x+2,4,self.format_value(tot_credit, tot_cur), Style.easyxf(header_style1))
                sheet.write(x+2,5,self.format_value(tot_debit-tot_credit, tot_cur),Style.easyxf(header_style1))
                x += 1
                sheet.write(x+2,2,'Total in BC', Style.easyxf(header_style1))
                sheet.write(x+2,3,self.format_value(tot_debit_bc, company_currency), Style.easyxf(header_style1))
                sheet.write(x+2,4,self.format_value(tot_credit_bc, company_currency), Style.easyxf(header_style1))
                sheet.write(x+2,5,self.format_value(tot_debit_bc-tot_credit_bc, company_currency),Style.easyxf(header_style1))
                x += 3
            x += 4
       
        file_data = BytesIO()
        report.save(file_data)
        file_data.seek(0)
        data1 = file_data.read()
        attachment_id = self.env['ir.attachment'].create({
                'name': 'PartnerLedger.xls',
                'datas': base64.b64encode(data1),
                }).id
        
        record_id = self.env['partner.ledger.download'].create({'excel_file': base64.b64encode(data1),'file_name': 'PartnerLedger.xls'},)
                
        return {'view_mode': 'form',
                'res_id': record_id.id,
                'res_model': 'partner.ledger.download',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'create': False, 'edit': False, 'delete': False} 
       }

class wizard_excel_report(models.TransientModel):
    _name= "partner.ledger.download"
    
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('Excel File', size=64)
