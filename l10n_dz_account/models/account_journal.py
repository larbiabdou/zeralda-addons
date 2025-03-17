from odoo import api, fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _default_outbound_payment_methods(self):
        res = super()._default_outbound_payment_methods()
        if self._is_payment_method_available('cheque'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_cheque_out')
        if self._is_payment_method_available('bank_cheque'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_bank_cheque_out')
        if self._is_payment_method_available('transfer'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_transfer_out')
        if self._is_payment_method_available('deposit'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_deposit_out')
        if self._is_payment_method_available('lc'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_lc_out')
        if self._is_payment_method_available('documentary_remittance'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_documentary_remittance_out')
        return res

    def _default_inbound_payment_methods(self):
        res = super()._default_inbound_payment_methods()
        if self._is_payment_method_available('cheque'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_cheque_in')
        if self._is_payment_method_available('bank_cheque'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_bank_cheque_in')
        if self._is_payment_method_available('transfer'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_transfer_in')
        if self._is_payment_method_available('deposit'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_deposit_in')
        if self._is_payment_method_available('lc'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_lc_in')
        if self._is_payment_method_available('documentary_remittance'):
            res |= self.env.ref('l10n_dz_account.account_payment_method_documentary_remittance_in')
        return res


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['check_printing'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['cheque'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['bank_cheque'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['transfer'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['deposit'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['lc'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['documentary_remittance'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res