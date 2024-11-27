from odoo import models, fields, api

class BankStatementLineWizard(models.TransientModel):
    _name = 'bank.statement.line.wizard'
    _description = 'Wizard for Creating Bank Statement Lines'

    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(string="Amount", required=True)
    reason = fields.Char(string="Reason")
    type = fields.Selection([
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('customer_cash_in', 'Customer Cash In'),
        ('supplier_cash_out', 'Supplier Cash Out')
    ], string="Type", required=True, default='cash_in')

    def action_create_statement_line(self):
        """Creates a bank statement line based on the wizard data"""
        statement_id = self.env.context.get('default_statement_id')
        statement_amount = self.amount if self.type in ('cash_in', 'customer_cash_in') else -1 * self.amount
        if not statement_id:
            return
        line_id = self.env['account.bank.statement.line'].create({
            'statement_id': statement_id,
            'partner_id': self.partner_id.id,
            'amount': statement_amount,
            'payment_ref': self.reason,
            'type': self.type,
        })
