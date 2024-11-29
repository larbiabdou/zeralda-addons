from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

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
    create_from_payment = fields.Boolean(
        string='create_from_payment',
        required=False)

    budget_post_id = fields.Many2one(
        comodel_name='account.budget.post',
        string='Reason',
        required=False)

    def button_undo_reconciliation(self):
        ''' Undo the reconciliation mades on the statement line and reset their journal items
        to their original states.
        '''
        self.line_ids.remove_move_reconcile()
        self.payment_ids.unlink()

        for st_line in self:
            st_line.with_context(force_delete=True).write({
                'to_check': False,
                'line_ids': [(5, 0)] + [(0, 0, line_vals) for line_vals in st_line._prepare_move_line_default_vals()],
            })

    def _create_payment(self, vals):
        """Créer un paiement en fonction du type."""
        Payment = self.env['account.payment']
        payment_type = False
        partner_type = False

        if vals.get('type') in ['customer_cash_in']:
            payment_type = 'inbound'
            partner_type = 'customer'
            payment_method_line_id = self.journal_id.inbound_payment_method_line_ids[0]
        elif vals.get('type') in ['supplier_cash_out']:
            payment_type = 'outbound'
            partner_type = 'supplier'
            payment_method_line_id = self.journal_id.outbound_payment_method_line_ids[0]

        if payment_type:
            payment_vals = {
                'partner_id': vals.get('partner_id'),
                'amount': abs(vals.get('amount', 0)),
                'payment_type': payment_type,
                'partner_type': partner_type,
                'create_from_statement': True,
                'journal_id': self.journal_id.id,  # Lié au journal du statement
                'payment_method_line_id': payment_method_line_id.id,  # Méthode de paiement manuelle
            }
            payment_id = Payment.create(payment_vals)
            return payment_id

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        """ Prepare the dictionary to create the default account.move.lines for the current account.bank.statement.line
        record.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        """
        self.ensure_one()

        if not counterpart_account_id:
            counterpart_account_id = self.journal_id.suspense_account_id.id
            if self.type == 'customer_cash_in':
                counterpart_account_id = self.partner_id.property_account_receivable_id.id
            elif self.type == 'supplier_cash_out':
                counterpart_account_id = self.partner_id.property_account_payable_id.id

        if not counterpart_account_id:
            raise UserError(_(
                "You can't create a new statement line without a suspense account set on the %s journal.",
                self.journal_id.display_name,
            ))

        company_currency = self.journal_id.company_id.sudo().currency_id
        journal_currency = self.journal_id.currency_id or company_currency
        foreign_currency = self.foreign_currency_id or journal_currency or company_currency

        journal_amount = self.amount
        if foreign_currency == journal_currency:
            transaction_amount = journal_amount
        else:
            transaction_amount = self.amount_currency
        if journal_currency == company_currency:
            company_amount = journal_amount
        elif foreign_currency == company_currency:
            company_amount = transaction_amount
        else:
            company_amount = journal_currency\
                ._convert(journal_amount, company_currency, self.journal_id.company_id, self.date)

        liquidity_line_vals = {
            'name': self.payment_ref,
            'move_id': self.move_id.id,
            'partner_id': self.partner_id.id,
            'account_id': self.journal_id.default_account_id.id,
            'currency_id': journal_currency.id,
            'amount_currency': journal_amount,
            'debit': company_amount > 0 and company_amount or 0.0,
            'credit': company_amount < 0 and -company_amount or 0.0,
        }

        # Create the counterpart line values.
        counterpart_line_vals = {
            'name': self.payment_ref,
            'account_id': counterpart_account_id,
            'move_id': self.move_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': foreign_currency.id,
            'amount_currency': -transaction_amount,
            'debit': -company_amount if company_amount < 0.0 else 0.0,
            'credit': company_amount if company_amount > 0.0 else 0.0,
        }
        return [liquidity_line_vals, counterpart_line_vals]

    def _get_accounting_amounts_and_currencies(self):
        """ Retrieve the transaction amount, journal amount and the company amount with their corresponding currencies
        from the journal entry linked to the statement line.
        All returned amounts will be positive for an inbound transaction, negative for an outbound one.

        :return: (
            transaction_amount, transaction_currency,
            journal_amount, journal_currency,
            company_amount, company_currency,
        )
        """
        self.ensure_one()
        liquidity_line, suspense_line, other_lines = self._seek_for_lines()
        if suspense_line and not other_lines:
            transaction_amount = -suspense_line[0].amount_currency
            transaction_currency = suspense_line[0].currency_id
        else:
            # In case of to_check or partial reconciliation, we can't trust the suspense line.
            transaction_amount = self.amount_currency if self.foreign_currency_id else self.amount
            transaction_currency = self.foreign_currency_id or liquidity_line.currency_id
        return (
            transaction_amount,
            transaction_currency,
            sum(liquidity_line.mapped('amount_currency')),
            liquidity_line.currency_id,
            sum(liquidity_line.mapped('balance')),
            liquidity_line.company_currency_id,
        )

    def _seek_for_lines(self):
        """ Helper used to dispatch the journal items between:
        - The lines using the liquidity account.
        - The lines using the transfer account.
        - The lines being not in one of the two previous categories.
        :return: (liquidity_lines, suspense_lines, other_lines)
        """
        liquidity_lines = self.env['account.move.line']
        suspense_lines = self.env['account.move.line']
        other_lines = self.env['account.move.line']
        partner_account_id = False
        if self.type == 'customer_cash_in':
            suspense_account = self.partner_id.property_account_receivable_id
        elif self.type == 'supplier_cash_out':
            suspense_account = self.partner_id.property_account_payable_id
        else:
            suspense_account = self.journal_id.suspense_account_id
        for line in self.move_id.line_ids:
            if line.account_id == self.journal_id.default_account_id:
                liquidity_lines += line
            elif line.account_id == suspense_account:
                suspense_lines += line
            else:
                other_lines += line
        if not liquidity_lines:
            liquidity_lines = self.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_cash', 'liability_credit_card'))
            other_lines -= liquidity_lines
        return liquidity_lines, suspense_lines, other_lines

    @api.depends('journal_id', 'currency_id', 'amount', 'foreign_currency_id', 'amount_currency',
                 'move_id.to_check',
                 'move_id.line_ids.account_id', 'move_id.line_ids.amount_currency',
                 'move_id.line_ids.amount_residual_currency', 'move_id.line_ids.currency_id',
                 'move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids')
    def _compute_is_reconciled(self):
        """ Compute the field indicating if the statement lines are already reconciled with something.
        This field is used for display purpose (e.g. display the 'cancel' button on the statement lines).
        Also computes the residual amount of the statement line.
        """
        for st_line in self:
            _liquidity_lines, suspense_lines, _other_lines = st_line._seek_for_lines()

            # Compute residual amount
            if st_line.to_check:
                st_line.amount_residual = -st_line.amount_currency if st_line.foreign_currency_id else -st_line.amount
            elif suspense_lines.account_id.reconcile:
                st_line.amount_residual = sum(suspense_lines.mapped('amount_residual_currency'))
            else:
                st_line.amount_residual = sum(suspense_lines.mapped('amount_currency'))

            # Compute is_reconciled
            if not st_line.id:
                # New record: The journal items are not yet there.
                st_line.is_reconciled = False
            elif suspense_lines:
                # In case of the statement line comes from an older version, it could have a residual amount of zero.
                if not suspense_lines.currency_id.is_zero(st_line.amount_residual) and not suspense_lines.currency_id.is_zero(abs(st_line.amount) - abs(st_line.amount_residual)):
                    st_line.is_reconciled = True
                else:
                    st_line.is_reconciled = suspense_lines.currency_id.is_zero(st_line.amount_residual)
            elif st_line.currency_id.is_zero(st_line.amount):
                st_line.is_reconciled = True
            else:
                # The journal entry seems reconciled.
                st_line.is_reconciled = True

    @api.model
    def create(self, vals):
        # Créer la ligne
        statement_line = super(AccountBankStatementLine, self).create(vals)
        # Créer un paiement si nécessaire
        if 'type' in vals and statement_line.type in ['customer_cash_in', 'supplier_cash_out'] and not statement_line.create_from_payment:
            payment_id =  statement_line._create_payment(vals)
            move_to_unlink = statement_line.move_id
            statement_line.move_id = payment_id.move_id.id
            move_to_unlink.button_draft()
            move_to_unlink.unlink()
            payment_id.move_id.action_post()
        return statement_line


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    date = fields.Date(
        compute=False,
        default=fields.Date.context_today,
        index=True,
    )
    name = fields.Char(
        string='Name',
        store=True,
        compute="_compute_name",
        required=False)
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        compute=False, check_company=False
    )

    move_ids = fields.Many2many(
        comodel_name='account.move',
        compute="_compute_move_ids",
        string='Move_ids')

    cashbox_start_id = fields.Many2one('account.bank.statement.cashbox', string="Starting Cashbox")
    cashbox_end_id = fields.Many2one('account.bank.statement.cashbox', string="Ending Cashbox")
    previous_statement_id = fields.Many2one('account.bank.statement', help='technical field to compute starting balance correctly', compute='_get_previous_statement', store=True)

    state = fields.Selection(string='Status', required=True, readonly=True, copy=False, tracking=True, selection=[
        ('draft', 'Draft'),
        ('open', 'New'),
        ('confirm', 'Validated'),
    ], default='draft',)

    difference = fields.Monetary(compute='compute_difference', store=True, help="Difference between the computed ending balance and the specified ending balance.")
    first_line_index = fields.Char(
        comodel_name='account.bank.statement.line',
        compute=False, index=False,
    )

    def _compute_date_index(self):
        return True
    def _check_cash_balance_end_real_same_as_computed(self):
        """ Check the balance_end_real (encoded manually by the user) is equals to the balance_end (computed by odoo).
            For a cash statement, if there is a difference, the different is set automatically to a profit/loss account.
        """
        for statement in self:
            if not statement.currency_id.is_zero(statement.difference):
                st_line_vals = {
                    'statement_id': statement.id,
                    'journal_id': statement.journal_id.id,
                    'amount': statement.difference,
                    'date': statement.date,
                }

                if statement.currency_id.compare_amounts(statement.difference, 0.0) < 0.0:
                    if not statement.journal_id.loss_account_id:
                        raise UserError(_(
                            "Please go on the %s journal and define a Loss Account. "
                            "This account will be used to record cash difference.",
                            statement.journal_id.name
                        ))

                    st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Loss)")
                    st_line_vals['counterpart_account_id'] = statement.journal_id.loss_account_id.id
                else:
                    # statement.difference > 0.0
                    if not statement.journal_id.profit_account_id:
                        raise UserError(_(
                            "Please go on the %s journal and define a Profit Account. "
                            "This account will be used to record cash difference.",
                            statement.journal_id.name
                        ))

                    st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Profit)")
                    st_line_vals['counterpart_account_id'] = statement.journal_id.profit_account_id.id

                self.env['account.bank.statement.line'].create(st_line_vals)
        return True

    @api.depends('balance_end_real', 'balance_end')
    def compute_difference(self):
        for statement in self:
            statement.difference = statement.balance_end_real - statement.balance_end

    def action_open(self):
        for record in self:
            record.state = 'open'

    def action_validate(self):
        for record in self:
            record._check_cash_balance_end_real_same_as_computed()
            record.state = 'confirm'

    def action_reopen(self):
        for record in self:
            record.state = 'open'

    def unlink(self):
        for record in self:
            if record.state not in ['draft']:
                raise ValidationError(_("You can not delete a posted Statement !"))
        return super().unlink()

    _sql_constraints = [
        ('unique_statement_per_day_per_journal',
         'UNIQUE(date, journal_id)',
         'Vous ne pouvez pas créer plusieurs relevés bancaires pour le même journal et le même jour.')
    ]

    @api.depends('date', 'journal_id')
    def _get_previous_statement(self):
        for st in self:
            # Search for the previous statement
            domain = [('date', '<=', st.date), ('journal_id', '=', st.journal_id.id)]
            # The reason why we have to perform this test is because we have two use case here:
            # First one is in case we are creating a new record, in that case that new record does
            # not have any id yet. However if we are updating an existing record, the domain date <= st.date
            # will find the record itself, so we have to add a condition in the search to ignore self.id
            #if not isinstance(st.id, models.NewId):
            domain.extend(['|', '&', ('id', '<', st.id), ('date', '=', st.date), '&', ('id', '!=', st.id), ('date', '!=', st.date)])
            previous_statement = self.search(domain, limit=1, order='date desc, id desc')
            st.previous_statement_id = previous_statement.id

    @api.depends('previous_statement_id', 'previous_statement_id.balance_end_real')
    def _compute_starting_balance(self):
        # When a bank statement is inserted out-of-order several fields needs to be recomputed.
        # As the records to recompute are ordered by id, it may occur that the first record
        # to recompute start a recursive recomputation of field balance_end_real
        # To avoid this we sort the records by date
        for statement in self.sorted(key=lambda s: s.date):
            if statement.previous_statement_id.balance_end_real != statement.balance_start:
                statement.balance_start = statement.previous_statement_id.balance_end_real
            else:
                # Need default value
                statement.balance_start = statement.balance_start or 0.0

    def _compute_move_ids(self):
        for record in self:
            record.move_ids = record.line_ids.move_id.ids

    def open_move_ids(self):
        return {
            'name': 'Moves',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'domain': [('id', 'in', self.move_ids.ids)],
        }

    def open_cash_in_wizard(self):
        return {
            'name': 'Create Cash In',
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_type': 'cash_in', 'default_statement_id': self.id},
        }

    def open_pay_wizard(self):
        return {
            'name': 'Pay Employee',
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_type': 'pay', 'default_statement_id': self.id},
        }

    def open_cash_out_wizard(self):
        return {
            'name': 'Create Cash Out',
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_type': 'cash_out', 'default_statement_id': self.id},
        }

    def open_customer_cash_in_wizard(self):
        return {
            'name': 'Create Customer Cash In',
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_type': 'customer_cash_in', 'default_statement_id': self.id},
        }
    def open_cashbox_id(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        if context.get('balance'):
            context['statement_id'] = self.id
            if context['balance'] == 'start':
                cashbox_id = self.cashbox_start_id.id
            elif context['balance'] == 'close':
                cashbox_id = self.cashbox_end_id.id
            else:
                cashbox_id = False

            action = {
                'name': _('Cash Control'),
                'view_mode': 'form',
                'res_model': 'account.bank.statement.cashbox',
                'view_id': self.env.ref('accounting_cash.view_account_bnk_stmt_cashbox_footer').id,
                'type': 'ir.actions.act_window',
                'res_id': cashbox_id,
                'context': context,
                'target': 'new'
            }

            return action
    def open_supplier_cash_out_wizard(self):
        return {
            'name': 'Create Supplier Cash Out',
            'type': 'ir.actions.act_window',
            'res_model': 'bank.statement.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_type': 'supplier_cash_out', 'default_statement_id': self.id},
        }

    @api.depends('date', 'journal_id')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.date and record.journal_id:
                date_str = record.date.strftime('%Y-%m-%d')  # Format de la date
                record.name = f"{record.journal_id.name} {date_str}"

class AccountBankStmtCashWizard(models.Model):
    """
    Account Bank Statement popup that allows entering cash details.
    """
    _name = 'account.bank.statement.cashbox'
    _description = 'Bank Statement Cashbox'
    _rec_name = 'id'

    cashbox_lines_ids = fields.One2many('account.cashbox.line', 'cashbox_id', string='Cashbox Lines')
    start_bank_stmt_ids = fields.One2many('account.bank.statement', 'cashbox_start_id')
    end_bank_stmt_ids = fields.One2many('account.bank.statement', 'cashbox_end_id')
    total = fields.Float(compute='_compute_total')
    currency_id = fields.Many2one('res.currency', compute='_compute_currency')

    @api.depends('start_bank_stmt_ids', 'end_bank_stmt_ids')
    def _compute_currency(self):
        for cashbox in self:
            cashbox.currency_id = False
            if cashbox.end_bank_stmt_ids:
                cashbox.currency_id = cashbox.end_bank_stmt_ids[0].currency_id
            if cashbox.start_bank_stmt_ids:
                cashbox.currency_id = cashbox.start_bank_stmt_ids[0].currency_id

    @api.depends('cashbox_lines_ids', 'cashbox_lines_ids.coin_value', 'cashbox_lines_ids.number')
    def _compute_total(self):
        for cashbox in self:
            cashbox.total = sum([line.subtotal for line in cashbox.cashbox_lines_ids])

    @api.model
    def default_get(self, fields):
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        balance = self.env.context.get('balance')
        statement_id = self.env.context.get('statement_id')
        if 'start_bank_stmt_ids' in fields and not vals.get('start_bank_stmt_ids') and statement_id and balance == 'start':
            vals['start_bank_stmt_ids'] = [(6, 0, [statement_id])]
        if 'end_bank_stmt_ids' in fields and not vals.get('end_bank_stmt_ids') and statement_id and balance == 'close':
            vals['end_bank_stmt_ids'] = [(6, 0, [statement_id])]

        return vals

    def name_get(self):
        result = []
        for cashbox in self:
            result.append((cashbox.id, str(cashbox.total)))
        return result

    @api.model_create_multi
    def create(self, vals):
        cashboxes = super(AccountBankStmtCashWizard, self).create(vals)
        cashboxes._validate_cashbox()
        return cashboxes

    def write(self, vals):
        res = super(AccountBankStmtCashWizard, self).write(vals)
        self._validate_cashbox()
        return res

    def _validate_cashbox(self):
        for cashbox in self:
            if cashbox.start_bank_stmt_ids:
                cashbox.start_bank_stmt_ids.write({'balance_start': cashbox.total})
            if cashbox.end_bank_stmt_ids:
                cashbox.end_bank_stmt_ids.write({'balance_end_real': cashbox.total})


class AccountBankStmtCloseCheck(models.TransientModel):
    """
    Account Bank Statement wizard that check that closing balance is correct.
    """
    _name = 'account.bank.statement.closebalance'
    _description = 'Bank Statement Closing Balance'

    def validate(self):
        bnk_stmt_id = self.env.context.get('active_id', False)
        if bnk_stmt_id:
            self.env['account.bank.statement'].browse(bnk_stmt_id).button_validate()
        return {'type': 'ir.actions.act_window_close'}
class AccountCashboxLine(models.Model):
    """ Cash Box Details """
    _name = 'account.cashbox.line'
    _description = 'CashBox Line'
    _rec_name = 'coin_value'
    _order = 'coin_value'

    @api.depends('coin_value', 'number')
    def _sub_total(self):
        """ Calculates Sub total"""
        for cashbox_line in self:
            cashbox_line.subtotal = cashbox_line.coin_value * cashbox_line.number

    coin_value = fields.Float(string='Coin/Bill Value', required=True, digits=0)
    number = fields.Integer(string='#Coins/Bills', help='Opening Unit Numbers')
    subtotal = fields.Float(compute='_sub_total', string='Subtotal', digits=0, readonly=True)
    cashbox_id = fields.Many2one('account.bank.statement.cashbox', string="Cashbox")
    currency_id = fields.Many2one('res.currency', related='cashbox_id.currency_id')




