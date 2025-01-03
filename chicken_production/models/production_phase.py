from odoo import models, fields

class ProductionPhase(models.Model):
    _name = 'production.phase'
    _description = 'Production Phase'

    # Basic fields
    name = fields.Char(string='Phase Name', required=True)
    code = fields.Char(string='Phase Code', required=True)
    duration = fields.Integer(string='Duration (days)', required=True)
    target_temperature = fields.Float(string='Target Temperature')
    target_humidity = fields.Float(string='Target Humidity')
    next_phase_id = fields.Many2one(
        'production.phase',
        string='Next Phase',
        help='Select the next phase in the production process.'
    )
    eggs_production = fields.Boolean(string='Eggs Production')

    # Products to Consume
    consume_product_ids = fields.Many2many(
        'product.product',
        relation="consume_product_ids",
        string='Products to Consume'
    )

    # Products to Declare
    declare_product_ids = fields.Many2many(
        'product.product',
        relation="declare_product_ids",
        string='Products to Declare'
    )

    type = fields.Selection(
        string='Type',
        selection=[('phase_1', 'Phase 1'),
                   ('phase_2', 'Phase 2'),
                   ('eggs_production', 'Eggs production'),],
        required=False, )
