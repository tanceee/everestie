from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class LandedCostTotal(models.Model):
    _name = 'landed.cost.total'

    def _default_account_comapny_id(self):
        return self.env.company

    stock_landed_cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost')
    cost_line_id = fields.Many2one('stock.landed.cost.lines', 'Cost Line')
    currency_id = fields.Many2one('res.currency', related='stock_landed_cost_id.currency_id')
    former_cost = fields.Monetary('Total')


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    stock_cost_line_total_ids = fields.One2many('landed.cost.total', 'stock_landed_cost_id')


    def _is_not_included(self, cost, val_line_values, cost_line):
        for valuation_line in cost.valuation_adjustment_lines:
            if cost_line.id == valuation_line.cost_line_id.id and val_line_values.get('product_id') == valuation_line.product_id.id:
                return True
        else:
            return False

    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids), ('is_included', '=', True)]).unlink()

        digits = self.env['decimal.precision'].precision_get('Product Price')
        towrite_dict = {}
        towrite_dict_plus = {}
        # for cost in self.filtered(lambda cost: cost.picking_ids):
        vales_by_line = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            # hide by smaak ----  total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()
            ignore_price = 0

            for val_line_values in all_val_line_values:
                egnore_count = 0
                ignore_price = 0
                for cost_line in cost.cost_lines:
                    if cost._is_not_included(cost, val_line_values, cost_line):
                        egnore_count += 1
                        continue
                    former_cost = val_line_values.get('former_cost', 0.0)
                    total_cost = tools.float_round(former_cost, precision_digits=digits) if digits else former_cost
                    if not vales_by_line.get(cost_line):
                        vales_by_line[cost_line] = {'total_qty': val_line_values.get('quantity', 0.0), 
                        'total_weight': val_line_values.get('weight', 0.0), 
                        'total_volume': val_line_values.get('volume', 0.0),
                        'total_cost': total_cost}
                    else:
                        vales_by_line[cost_line]['total_qty'] += val_line_values.get('quantity', 0.0)
                        vales_by_line[cost_line]['total_weight'] += val_line_values.get('weight', 0.0)
                        vales_by_line[cost_line]['total_volume'] += val_line_values.get('volume', 0.0)
                        vales_by_line[cost_line]['total_cost'] += total_cost
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                # if egnore_count < 1:
                #     total_qty += val_line_values.get('quantity', 0.0)
                #     total_weight += val_line_values.get('weight', 0.0)
                #     total_volume += val_line_values.get('volume', 0.0)
                    
                #     print(total_cost)
                #     # round this because former_cost on the valuation lines is also rounded
                #     total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost
                #     # hide by smaak ---- total_line += 1
                #     print("Cold ", total_cost)


            for line in cost.cost_lines:
                value_split = 0.0
                my_line_count = 0
                ignore_lines = cost.valuation_adjustment_lines.filtered(lambda x:not  x.is_included)
                count_ignore_cost_line = ignore_lines.filtered(lambda x: x.cost_line_id == line)
                line_is_included = cost.valuation_adjustment_lines.filtered(lambda x: x.is_included)
                count_costing_line = line_is_included.filtered(lambda x: x.cost_line_id == line)
                total_line_cost = line.price_unit
                for i in count_costing_line:
                    my_line_count +=1
                #smaak code ended
                for valuation in count_costing_line:
                    value = 0.0
                    # if total_line == 0:
                    #     continue
                    total_line = my_line_count
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and vales_by_line[line].get('total_qty'):
                            per_unit = (line.price_unit / vales_by_line[line].get('total_qty'))
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and vales_by_line[line].get('total_weight'):
                            per_unit = (line.price_unit / vales_by_line[line].get('total_weight'))
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and vales_by_line[line].get('total_volume'):
                            per_unit = (line.price_unit / vales_by_line[line].get('total_volume'))
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and vales_by_line[line].get('total_cost'):
                            if count_ignore_cost_line:
                                per_unit = (line.price_unit / vales_by_line[line].get('total_cost'))
                            else:
                                per_unit = (line.price_unit / vales_by_line[line].get('total_cost'))
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value

        for key, value in towrite_dict.items():
            line = AdjustementLines.browse(key)
            line.write({'additional_landed_cost': value})

            if line.cost_line_id not in towrite_dict_plus:
                towrite_dict_plus[line.cost_line_id] = line.additional_landed_cost
            else:
                towrite_dict_plus[line.cost_line_id] += line.additional_landed_cost

        if self.stock_cost_line_total_ids:
            self.stock_cost_line_total_ids = [(5,0,0)]

        for key, value in towrite_dict_plus.items():
            self.env['landed.cost.total'].create({
                'stock_landed_cost_id': self.id,
                'cost_line_id': key.id,
                'former_cost': value
            }) 
        return True


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    is_included = fields.Boolean('Include', default=True)

    @api.onchange('is_included')
    def onchnage_is_included(self):
        self.additional_landed_cost = 0
        
        
    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        print("----stock.valuation.adjustment.lines inherited----")
        AccountMoveLine = []
    
        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])
    
        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            print("this is the quantity",self.quantity)
            if self.quantity ==0:
                quantity =1
            else:
                quantity = self.quantity
            diff = diff * qty_out / quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append([0, 0, debit_line])
            AccountMoveLine.append([0, 0, credit_line])
    
            if self.env.company.anglo_saxon_accounting:
                expense_account_id = self.product_id.product_tmpl_id.get_product_accounts()['expense'].id
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=0,
                                  account_id=expense_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)
    
                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])
        return AccountMoveLine
        # return super(AdjustmentLines,self)._create_account_move_line(move, credit_account_id, debit_account_id, qty_out, already_out_account_id)
    

        
        
        
        
        
        
        
        
