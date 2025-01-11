from odoo import api, fields, models

class ProduceWizardParent(models.TransientModel):
    _name = 'produce.wizard'
    _description = 'ProduceWizardParent'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production")
    line_ids = fields.One2many(
        comodel_name='produce.wizard.line',
        inverse_name='wizard_id',
        string='Lines',
        required=False)
    type = fields.Selection(
        string='Type',
        selection=[('loss', 'Loss'),
                   ('declaration', 'Declaration')],
        required=False, )

    date = fields.Date(string="Dateé",
                       default=fields.Date.context_today,
                       )
    domain_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_product_ids",
        string='Domain_product_ids')

    domain_consumed_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_consumed_product_ids",
        string='Domain_product_ids')

    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Domain_lot_ids')

    phase_type = fields.Selection(
        string='Type',
        selection=[('phase_1', 'Phase 1'),
                   ('phase_2', 'Phase 2'),
                   ('eggs_production', 'Eggs production'), ],
        related="chick_production_id.type",
        required=False, )

    def action_validate_production(self):
        for line in self.line_ids:
            line.action_validate_production()

class ProduceWizard(models.TransientModel):
    _name = 'produce.wizard.line'
    _description = 'Produce Wizard'

    wizard_id = fields.Many2one(
        comodel_name='produce.wizard',
        string='Wizard',
        required=False)

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", related="wizard_id.chick_production_id")
    domain_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_product_ids",
        related="wizard_id.domain_product_ids",
        string='Domain_product_ids')
    domain_consumed_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_consumed_product_ids",
        related="wizard_id.domain_consumed_product_ids",
        string='Domain_product_ids')

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
        related="wizard_id.domain_lot_ids",
        #compute='compute_domain_lot_ids',
        #store=True,
        string='Domain_lot_ids')

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], related='product_to_consume_id.gender',
        store=True,
        string="Gender Animal")

    average_weight = fields.Float(
        string='Eggs average weight',
        required=False)

    weight_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Uom',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        required=False)

    # remaining_quantity = fields.Integer(
    #     string='Remaining_quantity',
    #     compute="compute_quantity_remaining",
    #     required=False)

    unit_cost = fields.Float(
        string='Unit cost',
        required=False)

    # def compute_quantity_remaining(self):
    #     for record in self:
    #         declarations = self.env['product.declaration'].search([('declaration_id', '=', record.id), ('type', '=', 'raw')])
    #         quantity_used = sum(declaration.quantity for declaration in declarations) or 0
    #         record.remaining_quantity = record.quantity - quantity_used

    def action_validate_production(self):
        location_production = self.env['stock.location'].search([('usage', '=', 'production')])
        for record in self:
            production = record.chick_production_id
            #record.remaining_quantity = record.quantity
            if record.wizard_id.type != 'loss':
                record.lot_id = self.env['stock.lot'].create({
                    'product_id': record.product_id.id,
                    'name': record.lot_name,
                    'company_id': self.env.company.id,
                })

            # Create stock picking for product consumption
                if record.wizard_id.phase_type == 'incubation':
                    unit_cost = record.chick_production_id.unitary_eggs_cost
                elif record.wizard_id.phase_type != 'eggs_production':
                    unit_cost = record.chick_production_id.male_unitary_cost if record.product_id.gender == 'male' else record.chick_production_id.female_unitary_cost
                else:
                    unit_cost = record.chick_production_id.total_cost / record.quantity
                record.unit_cost = unit_cost
                declaration_picking = self.env['stock.picking'].create({
                    'partner_id': False,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                    'location_id': location_production.id,
                    'location_dest_id': record.chick_production_id.building_id.stock_location_id.id,
                })
                move_id = self.env['stock.move'].create({
                    'picking_id': declaration_picking.id,
                    'name': record.product_id.name,
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.quantity,
                    'product_uom': record.uom_id.id,
                    'price_unit': unit_cost,
                    'location_id': location_production.id,
                    'location_dest_id': record.chick_production_id.building_id.stock_location_id.id,
                    'quantity': record.quantity,
                    'move_line_ids': [(0, 0, {
                        'product_id': record.product_id.id,
                        'product_uom_id': record.uom_id.id,
                        'quantity': record.quantity,
                        'location_id': location_production.id,
                        'location_dest_id': record.chick_production_id.building_id.stock_location_id.id,
                        'lot_id': record.lot_id.id if record.lot_id else False,
                    })]
                })

                declaration_picking.button_validate()
                record.cost = sum(line.value for line in declaration_picking.move_ids.stock_valuation_layer_ids.filtered(
                    lambda l: l.product_id == record.product_id))
            if record.wizard_id.phase_type != 'eggs_production':
                consumption_picking = self.env['stock.picking'].create({
                    'partner_id': False,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                    'location_id': record.chick_production_id.building_id.stock_location_id.id,
                    'location_dest_id': location_production.id,
                    'move_ids': [(0, 0, {
                        'name': record.product_to_consume_id.name,
                        'product_id': record.product_to_consume_id.id,
                        'product_uom_qty': record.quantity,
                        'product_uom': record.uom_id.id,
                        'location_id': record.chick_production_id.building_id.stock_location_id.id,
                        'location_dest_id': location_production.id,
                        'quantity': record.quantity,
                        'move_line_ids': [(0, 0, {
                            'product_id': record.product_to_consume_id.id,
                            'product_uom_id': record.uom_id.id,
                            'quantity': record.quantity,
                            'location_id': record.chick_production_id.building_id.stock_location_id.id,
                            'location_dest_id': location_production.id,
                            'lot_id': record.initial_lot_id.id if record.initial_lot_id else False,
                        })]
                    })],
                })
                consumption_picking.button_validate()
                if record.wizard_id.type == 'loss':
                    record.cost = sum(line.value for line in consumption_picking.move_ids.stock_valuation_layer_ids.filtered(
                        lambda l: l.product_id == record.product_to_consume_id))
                declaration_id = self.env['product.declaration'].create({
                    'chick_production_id': record.chick_production_id.id,
                    'product_id': record.product_id.id if record.product_id else False,
                    'product_to_consume_id': record.product_to_consume_id.id if record.product_to_consume_id else False,
                    'uom_id': record.uom_id.id,
                    'lot_id': record.lot_id.id if record.lot_id else False,
                    'initial_lot_id': record.initial_lot_id.id if record.initial_lot_id else False,
                    'cost': record.cost,
                    'type': record.wizard_id.type,
                    'gender': record.gender,
                    'quantity': record.quantity,
                    'date': record.wizard_id.date,
                })
            #record.state = 'confirmed'
