from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    create_from_statement = fields.Boolean(
        string='Create_from_statement',
        required=False)

    def action_post(self):
        if self.journal_id.type == 'cash' and not self.create_from_statement:
            statement_id = self.env['account.bank.statement'].search([('date', '=', self.date), ('state', '=', 'posted'), ('journal_id', '=', self.journal_id.id)])
            if not statement_id:
                raise ValidationError(_('There is no statement opened this day'))
            else:
                type = 'customer_cash_in' if self.partner_type == 'customer' else 'supplier_cash_out'
                amount = self.amount if self.payment_type == 'inbound' else -1 * self.amount
                statement_line = self.env['account.bank.statement.line'].create({
                    'type': type,
                    'create_from_payment': True,
                    'amount': amount,
                    'partner_id': self.partner_id.id,
                    'date': self.date,
                    'statement_id': statement_id[0].id,
                    'payment_ref': self.ref,
                })
                move_to_unlink = statement_line.move_id
                statement_line.move_id = self.move_id.id
                move_to_unlink.button_draft()
                move_to_unlink.unlink()
               # payment_id.move_id.action_post()
        return super(AccountPayment, self).action_post()
