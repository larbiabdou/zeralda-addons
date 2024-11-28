from odoo import models, fields, api

class BankStatementLineWizard(models.TransientModel):
    _name = 'bank.statement.line.wizard'
    _description = 'Wizard for Creating Bank Statement Lines'

    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(string="Amount", required=True)
    reason = fields.Char(string="Ref")
    type = fields.Selection([
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('customer_cash_in', 'Customer Cash In'),
        ('supplier_cash_out', 'Supplier Cash Out'),
        ('pay', 'Pay Employee')
    ], string="Type", required=True, default='cash_in')
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False)
    budget_post_id = fields.Many2one(
        comodel_name='account.budget.post',
        string='Reason',
        required=False)
    def action_create_statement_line(self):
        """Creates a bank statement line based on the wizard data"""
        statement_id = self.env.context.get('default_statement_id')
        statement_amount = self.amount if self.type in ('cash_in', 'customer_cash_in', 'pay') else -1 * self.amount
        if not statement_id:
            return
        line_id = self.env['account.bank.statement.line'].create({
            'statement_id': statement_id,
            'partner_id': self.partner_id.id,
            'amount': statement_amount,
            'payment_ref': self.reason,
            'employee_id': self.employee_id.id,
            'type': self.type,
            'budget_post_id': self.budget_post_id.id,
        })
