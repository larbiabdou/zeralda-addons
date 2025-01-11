from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    building_id = fields.Many2one(
        comodel_name='chicken.building',
        string='Building',
        required=False)

    def get_declarations(self):
        self.line_ids = [(5, 0, 0)]
        lines = self.production_id.product_declaration_ids
        data = []
        for line in lines:
            data.append([0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'quantity_to_use': line.quantity,
                'uom_id': line.uom_id.id,
                'lot_id': line.lot_id.id,
            }])
        self.line_ids = data
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'chick.production.next.phase.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }

    def confirm_next_phase(self):
        male_quantity = sum(line.quantity for line in self.line_ids.filtered(lambda l: l.product_id.gender == 'male'))
        female_quantity = sum(line.quantity for line in self.line_ids.filtered(lambda l: l.product_id.gender == 'female'))
        if self.production_id.phase_id.type in ['phase_1', 'phase_2']:
            next_production_id = self.env['chick.production'].create({
                'phase_id': self.next_phase_id.id,
                'previous_production_id': self.production_id.id,
                'start_date': self.start_date,
                'male_quantity': male_quantity,
                'project_id': self.production_id.project_id.id,
                'female_quantity': female_quantity,
            })
            data = []
            for line in self.line_ids:
                if line.quantity_to_use > 0:
                    data.append([0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.quantity_to_use,
                        'uom_id': line.uom_id.id,
                        'lot_id': line.lot_id.id,
                       # 'unit_cost': line.unit_cost,
                        'type': 'raw',
                    }])
            next_production_id.product_component_ids = data
            self.production_id.next_production_id = next_production_id.id

class ChickProductionNextPhaseLine(models.TransientModel):
    _name = 'chick.production.next.phase.line'
    _description = 'Lines for Next Production Phase'

    wizard_id = fields.Many2one('chick.production.next.phase.wizard', string="Wizard", required=True, ondelete='cascade')
    # domain_product_ids = fields.Many2many(
    #     comodel_name='product.product',
    #     string='Domain_product_ids')
    # domain_lot_ids = fields.Many2many(
    #     comodel_name='stock.lot',
    #     string='Domain_lot_ids')

    product_id = fields.Many2one('product.product', string="Product to Declare", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    quantity_to_use = fields.Float(string="Quantity to use")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_unit').id)])
    lot_id = fields.Many2one('stock.lot', string="Lot")
    tracking = fields.Selection(
        string='Tracking',
        related="product_id.tracking",
        store=True,
        required=False, )

    @api.constrains('quantity_to_use', 'quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity_to_use > record.quantity:
                raise ValidationError('La quantité à utiliser ne peut pas dépasser la quantité restante!')

            if record.quantity_to_use < 0:
                raise ValidationError('La quantité à utiliser doit être positive!')
