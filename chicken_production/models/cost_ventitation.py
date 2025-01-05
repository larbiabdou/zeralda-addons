from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CostVentilation(models.Model):
    _name = 'cost.ventilation'
    _description = 'Cost Ventilation'

    name = fields.Char(string="Name", required=True)
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    type = fields.Selection([
        ('service', 'Service'),
        ('salary', 'Salary')
    ], string="Type", required=True)
    production_ids = fields.Many2many('chick.production', string="Productions", required=True)
    amount = fields.Float(string="Amount", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
    ], string="State", default='draft', readonly=True)
    cost_ids = fields.One2many('chick.production.cost', 'ventilation_id', string="Costs")

    @api.model
    def _get_total_quantity(self, productions):
        total_male = sum(production.quantity_male_remaining for production in productions)
        total_female = sum(production.quantity_female_remaining for production in productions)
        return total_male, total_female

    def action_validate(self):
        if not self.production_ids:
            raise UserError(_("Please select productions to ventilate costs."))
        if self.amount <= 0:
            raise UserError(_("Amount must be greater than 0."))

        total_male, total_female = self._get_total_quantity(self.production_ids)
        total_quantity = total_male + total_female
        if total_quantity == 0:
            raise UserError(_("Total quantity (male + female) is zero, cost distribution not possible."))

        for production in self.production_ids:
            # Male cost
            male_cost = self.amount * production.quantity_male_remaining / total_quantity
            self.env['chick.production.cost'].create({
                'name': self.name,
                'resource': self.name,
                'chick_production_id': production.id,
                'type': self.type,
                'amount': male_cost,
                'gender': 'male',
                'ventilation_id': self.id,
                'date': self.date,
            })

            # Female cost
            female_cost = self.amount * production.quantity_female_remaining / total_quantity
            self.env['chick.production.cost'].create({
                'name': self.name,
                'resource': self.name,
                'chick_production_id': production.id,
                'type': self.type,
                'amount': female_cost,
                'gender': 'female',
                'ventilation_id': self.id,
                'date': self.date,
            })

        self.state = 'validated'
