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
    consume_product_ids = fields.One2many(
        'production.phase.product.consume',
        'phase_id',
        string='Products to Consume'
    )

    # Products to Declare
    declare_product_ids = fields.One2many(
        'production.phase.product.declare',
        'phase_id',
        string='Products to Declare'
    )


class ProductionPhaseProductConsume(models.Model):
    _name = 'production.phase.product.consume'
    _description = 'Product to Consume'

    phase_id = fields.Many2one('production.phase', string='Phase', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)


class ProductionPhaseProductDeclare(models.Model):
    _name = 'production.phase.product.declare'
    _description = 'Product to Declare'

    phase_id = fields.Many2one('production.phase', string='Phase', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
