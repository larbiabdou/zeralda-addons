from odoo import models, fields, api

class ChickProductionCost(models.Model):
    _name = 'chick.production.cost'
    _description = 'Coûts de production'

    name = fields.Char(
        string='Name',
        required=False)

    chick_production_id = fields.Many2one('chick.production', string='Production', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    type = fields.Selection([
        ('input', 'Intrant'),
        ('equipment', 'Équipement'),
        ('reception', 'Reception'),
        ('service', 'Service'),
        ('salary', 'Salary'),
    ], string='Type', required=True)
    amount = fields.Float(string='Montant', digits='Product Price')
    resource = fields.Char(string='Ressource')
    equipment_id = fields.Many2one('maintenance.equipment', string='Équipement')
    product_id = fields.Many2one('product.product', string='Produit')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender Animal", required=True)
    ventilation_id = fields.Many2one('cost.ventilation', string="Ventilation")

    @api.model
    def create(self, values):
        # Add code here
        production = self.env['chick.production'].browse(values.get("chick_production_id"))
        if not (production.type != 'phase_1' and values['type'] == 'reception'):
            self.env['account.analytic.line'].create({
                'name': values['name'],
                'account_id': production.project_id.analytic_account_id.id,
                'amount': -1 * values['amount'],
                'chick_production_id': values['chick_production_id'],
            })
        return super(ChickProductionCost, self).create(values)