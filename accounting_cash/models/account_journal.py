from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def open_action(self):
        # EXTENDS account
        # set default action for liquidity journals in dashboard

        if self.type == 'cash' and not self._context.get('action_name'):
            self.ensure_one()
            action = self.env['ir.actions.actions']._for_xml_id('account.action_view_bank_statement_tree')
            action['context'] = {'default_journal_id': self.id}
            action['domain'] = [('journal_id', '=', self.id)]
            action['view_mode'] = 'tree,form'
            return action
        return super().open_action()
