from odoo import api, fields, models


class ProductDeclaration(models.TransientModel):
    _name = 'product.declaration'
    _description = 'Product declaration'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", )

    declaration_id = fields.Many2one(
        comodel_name='product.declaration',
        string='Declaration_id',
        required=False)
    product_id = fields.Many2one('product.product', string="Product to Declare")
    product_to_consume_id = fields.Many2one('product.product', string="Product to Consume")
    quantity = fields.Float(string="Quantity", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_unit').id)],)
    lot_name = fields.Char(string="Lot")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    initial_lot_id = fields.Many2one('stock.lot', string="Initial Lot")
    cost = fields.Float(string="Cost")
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        #compute='compute_domain_lot_ids',
        #store=True,
        string='Domain_lot_ids')

    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirmed', 'Confirmed'), ],
        default='draft',
        required=False, )

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], related='product_to_consume_id.gender',
        store=True,
        string="Gender Animal")

    type = fields.Selection(
        string='Type',
        selection=[('loss', 'Loss'),
                   ('declaration', 'Declaration'),
                   ('raw', 'Raw'),],
        required=False, )

    date = fields.Date(string="Dateé",
        default=fields.Date.context_today,
    )

    phase_type = fields.Selection(
        string='Type',
        store=True,
        related="chick_production_id.type",
        required=False, )

    average_weight = fields.Float(
        string='Eggs average weight',
        required=False)

    weight_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Uom',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        required=False)

    remaining_quantity = fields.Integer(
        string='Remaining_quantity',
        compute="compute_quantity_remaining",
        required=False)

    unit_cost = fields.Float(
        string='Unit cost',
        required=False)

    def compute_quantity_remaining(self):
        for record in self:
            declarations = self.env['product.declaration'].search([('declaration_id', '=', record.id), ('type', '=', 'raw')])
            quantity_used = sum(declaration.quantity for declaration in declarations) or 0
            record.remaining_quantity = record.quantity - quantity_used