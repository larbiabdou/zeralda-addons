from odoo import models, fields, api

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

   # cost = fields.Float(string='Coût', digits='Product Price')
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unité de mesure',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_wtime').id)],
    )
    capacity = fields.Integer(
        string='Capacity',
        required=False)
    
    cost_per_unit = fields.Float(
        string='Cost per unit',
        required=False)