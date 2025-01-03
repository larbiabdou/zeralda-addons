from odoo import models, fields, api

class ChickProductionNextPhaseWizard(models.TransientModel):
    _name = 'chick.production.next.phase.wizard'
    _description = 'Wizard for Next Production Phase'

    production_id = fields.Many2one('chick.production', string="Current Production", required=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, required=True)
    line_ids = fields.One2many('chick.production.next.phase.line', 'wizard_id', string="Products to Declare")
    domain_product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Domain_product_ids')
    next_phase_id = fields.Many2one(
        comodel_name='production.phase',
        string='Next phase',
        required=False)
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Domain_lot_ids')

    def confirm_next_phase(self):
        male_quantity = sum(line.quantity for line in self.line_ids.filtered(lambda l: l.product_id.gender == 'male'))
        female_quantity = sum(line.quantity for line in self.line_ids.filtered(lambda l: l.product_id.gender == 'female'))
        if self.production_id.phase_id.type == 'phase_1':
            next_production_id = self.env['chick.production'].create({
                'phase_id': self.next_phase_id.id,
                'previous_production_id': self.production_id.id,
                'start_date': self.start_date,
                'male_quantity': male_quantity,
                'female_quantity': female_quantity,
            })
            self.production_id.next_production_id = next_production_id.id



class ChickProductionNextPhaseLine(models.TransientModel):
    _name = 'chick.production.next.phase.line'
    _description = 'Lines for Next Production Phase'

    wizard_id = fields.Many2one('chick.production.next.phase.wizard', string="Wizard", required=True, ondelete='cascade')
    domain_product_ids = fields.Many2many(
        comodel_name='product.product',
        related="wizard_id.domain_product_ids",
        string='Domain_product_ids')
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        related="wizard_id.domain_lot_ids",
        string='Domain_lot_ids')
    product_id = fields.Many2one('product.product', string="Product to Declare", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_unit').id)])
    lot_id = fields.Many2one('stock.lot', string="Lot")
