from odoo import models, fields

class ChickenBuilding(models.Model):
    _name = 'chicken.building'
    _description = 'Chicken Building'

    name = fields.Char(string='Name', required=True)
    building_capacity = fields.Integer(string='Building Capacity', required=True)
    building_location = fields.Char(string='Building Location')
    last_inspection_date = fields.Date(string='Last Day of Inspection')
    stock_location_id = fields.Many2one(
        'stock.location',
        string='Stock Location',
        required=False,
        help="Physical stock location associated with this building."
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=False)