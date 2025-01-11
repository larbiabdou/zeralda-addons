from odoo import models, fields, api
from odoo.exceptions import ValidationError


class IncubationWizard(models.TransientModel):
    _name = 'incubation.wizard'
    _description = 'Wizard for Next Production Phase'

    chick_production_id = fields.Many2one('chick.production', string="Current Production", required=True)
    line_ids = fields.One2many('incubation.wizard.line', 'wizard_id', string="Declarations")
    capacity = fields.Integer(
        string='Capacity',
        related='chick_production_id.capacity',
        required=False)
    phase_type = fields.Selection(
        string='Type',
        selection=[('phase_1', 'Phase 1'),
                   ('phase_2', 'Phase 2'),
                   ('eggs_production', 'Eggs production'), ],
        related="chick_production_id.type",
        required=False, )

    def get_eggs_declarations(self):
        self.line_ids = [(5, 0, 0)]
        if self.phase_type == 'incubation':
            declarations = self.env['product.declaration'].search([('chick_production_id.project_id', '=', self.chick_production_id.project_id.id),
                                                              ('phase_type', '=', 'eggs_production'), ('type', '=', 'declaration')])
            data = []
            for declaration in declarations:
                data.append([0, 0, {
                    'chick_production_id': declaration.chick_production_id.id,
                    'declaration_id': declaration.id,
                    'product_id': declaration.product_id.id,
                    'quantity_remaining': declaration.remaining_quantity,
                    'uom_id': declaration.uom_id.id,
                    'unit_cost': declaration.unit_cost,
                    'lot_id': declaration.lot_id.id,
                }])
        elif self.phase_type == 'phase_1':
            lines = self.chick_production_id.import_folder.purchase_order_ids.picking_ids.move_line_ids
            data = []
            for line in lines:
                data.append([0, 0, {
                    'product_id': line.product_id.id,
                    'quantity_remaining': line.quantity,
                    'uom_id': line.product_uom_id.id,
                    'lot_id': line.lot_id.id,
                }])
        self.line_ids = data
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'incubation.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }

    def action_validate(self):
        data = []
        for line in self.line_ids:
            data.append([0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity_to_use,
                'declaration_id': line.declaration_id.id,
                'uom_id': line.uom_id.id,
                'lot_id': line.lot_id.id,
                'unit_cost': line.unit_cost,
                'type': 'raw',
            }])
        self.chick_production_id.product_component_ids = [(5, 0, 0)]
        self.chick_production_id.product_component_ids = data

    @api.constrains('line_ids', 'line_ids.quantity_to_use.', 'capacity')
    def _check_quantity(self):
        for record in self:
            if record.capacity < sum(line.quantity_to_use for line in record.line_ids) and record.phase_type == 'incubation':
                raise ValidationError('La quantité à utiliser ne peut pas dépasser la capacité!')

class IncubationWizardLine(models.TransientModel):
    _name = 'incubation.wizard.line'
    _description = 'Lines for Next Production Phase'

    wizard_id = fields.Many2one('incubation.wizard', string="Wizard", required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product to Declare", required=True)
    quantity_remaining = fields.Float(string="Quantity",)
    chick_production_id = fields.Many2one('chick.production', string="Production",)

    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_unit').id)])
    lot_id = fields.Many2one('stock.lot', string="Lot")
    quantity_to_use = fields.Float(
        string='Quantity to use',
        required=False)
    declaration_id = fields.Many2one(
        comodel_name='product.declaration',
        string='Declaration_id',
        required=False)

    unit_cost = fields.Float(
        string='Unit cost',
        required=False)

    tracking = fields.Selection(
        string='Tracking',
        related="product_id.tracking",
        store=True,
        required=False, )

    @api.constrains('quantity_to_use', 'quantity_remaining')
    def _check_quantity(self):
        for record in self:
            if record.quantity_to_use > record.quantity_remaining:
                raise ValidationError('La quantité à utiliser ne peut pas dépasser la quantité restante!')

            if record.quantity_to_use < 0:
                raise ValidationError('La quantité à utiliser doit être positive!')

    def validate_quantity(self):
        for record in self:
            return True

