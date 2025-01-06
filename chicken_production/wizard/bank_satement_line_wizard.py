from odoo import models, fields, api
from datetime import date


class BankStatementLineWizard(models.TransientModel):
    _inherit = 'bank.statement.line.wizard'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=False)

    def _prepare_bank_statement_vales(self):
        values = super()._prepare_bank_statement_vales()
        values['project_id'] = self.project_id.id
        return values

    def action_create_statement_line(self):
        """Creates a bank statement line based on the wizard data"""
        super().action_create_statement_line()
        if self.type in ('cash_out', 'customer_cash_out', 'pay'):
            productions = self.env['chick.production'].search([('project_id', '=', self.project_id.id), ('state', '=', 'in_progress')])
            total_male = sum(production.quantity_male_remaining for production in productions)
            total_female = sum(production.quantity_female_remaining for production in productions)
            total_quantity = total_male + total_female

            for production in productions:
                # Male cost
                male_cost = self.amount * production.quantity_male_remaining / total_quantity
                self.env['chick.production.cost'].create({
                    'name': self.reason,
                    'resource': self.reason,
                    'chick_production_id': production.id,
                    'type': 'service',
                    'amount': male_cost,
                    'gender': 'male',
                    'date': date.today(),
                })

                # Female cost
                female_cost = self.amount * production.quantity_female_remaining / total_quantity
                self.env['chick.production.cost'].create({
                    'name': self.reason,
                    'resource': self.reason,
                    'chick_production_id': production.id,
                    'type': 'service',
                    'amount': female_cost,
                    'gender': 'female',
                    'date': date.today(),
                })
