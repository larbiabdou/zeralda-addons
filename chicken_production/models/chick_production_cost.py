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
        ('reception', 'Reception')
    ], string='Type', required=True)
    amount = fields.Float(string='Montant', digits='Product Price')
    resource = fields.Char(string='Ressource')
    equipment_id = fields.Many2one('maintenance.equipment', string='Équipement')
    product_id = fields.Many2one('product.product', string='Produit')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender Animal", required=True)