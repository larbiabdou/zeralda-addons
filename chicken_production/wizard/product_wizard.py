from odoo import api, fields, models


class ProduceWizard(models.Model):
    _name = 'produce.wizard'
    _description = 'Produce Wizard'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", required=True)
    domain_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_product_ids",
        string='Domain_product_ids')
    domain_consumed_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation="domain_consumed_product_ids",
        string='Domain_product_ids')
    product_id = fields.Many2one('product.product', string="Product to Declare")
    product_to_consume_id = fields.Many2one('product.product', string="Product to Consume", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    lot_name = fields.Char(string="Lot")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    initial_lot_id = fields.Many2one('stock.lot', string="Initial Lot")
    cost = fields.Float(string="Cost")
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        compute='compute_domain_lot_ids',
        store=True,
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
                   ('declaration', 'Declaration'), ],
        required=False, )

    @api.depends('product_to_consume_id')
    def compute_domain_lot_ids(self):
        for record in self:
            record.domain_lot_ids = False
            lines = record.chick_production_id.import_folder.purchase_order_ids.picking_ids.move_line_ids.filtered(
                lambda l: l.product_id == record.product_to_consume_id) if record.chick_production_id.import_folder.purchase_order_ids and self.chick_production_id.import_folder.purchase_order_ids.picking_ids else \
                False
            if lines:
                record.domain_lot_ids = lines.lot_id.ids

    def action_validate_production(self):
        location_production = self.env['stock.location'].search([('usage', '=', 'production')])
        for record in self:
            production = record.chick_production_id
            if record.type != 'loss':
                record.lot_id = self.env['stock.lot'].create({
                    'product_id': record.product_id.id,
                    'name': record.lot_name,
                    'company_id': self.env.company.id,
                })
            # Create stock picking for product consumption

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
                    'price_unit': record.chick_production_id.male_unitary_cost if record.product_id.gender == 'male' else record.chick_production_id.female_unitary_cost,
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
                record.cost = sum(line.value for line in declaration_picking.move_ids.stock_valuation_layer_ids.filtered(
                    lambda l: l.product_id == record.product_id))

                declaration_picking.button_validate()

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
            record.state = 'confirmed'
