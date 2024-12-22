from odoo import models, fields, api, _
from datetime import timedelta

from odoo.exceptions import ValidationError


class ChickProduction(models.Model):
    _name = 'chick.production'
    _description = 'Chick Production'

    # Basic fields
    name = fields.Char(string='Name', required=True, default=lambda self: self._generate_name(), )
    start_date = fields.Date(string='Start Date', required=True)
    phase_id = fields.Many2one('production.phase', string='Phase', required=True)
    estimated_end_date = fields.Date(string='Estimated End Date', compute='_compute_estimated_end_date', store=True)

    # Import Folder and Reception Details
    import_folder = fields.Many2one('import.folder', string='Import Folder')
    reception_date = fields.Date(string='Reception Date', store=True)

    # Male and Female Quantities and Costs
    male_quantity = fields.Float(string='Male Quantity', )
    male_unitary_cost = fields.Float(string='Male Unitary Cost', )
    female_quantity = fields.Float(string='female Quantity', )
    female_unitary_cost = fields.Float(string='female Unitary Cost', )

    # Remaining Quantities
    quantity_male_remaining = fields.Float(string='Quantity Male Remaining', compute='_compute_remaining_quantities', store=True)
    quantity_female_remaining = fields.Float(string='Quantity female Remaining', compute='_compute_remaining_quantities', store=True)

    # Mortality Rates
    male_mortality_rate = fields.Float(string='Male Mortality Rate (%)', compute='_compute_mortality_rates', store=True)
    female_mortality_rate = fields.Float(string='female Mortality Rate (%)', compute='_compute_mortality_rates', store=True)

    # Building and Day/Week
    building_id = fields.Many2one('chicken.building', string='Building')
    day = fields.Integer(string='Day', default=1)
    week = fields.Integer(string='Week', compute='_compute_week', store=True)

    # Costs
    total_cost = fields.Float(string='Total Cost', compute='compute_total_cost', store=True)
    total_male_cost = fields.Float(string='Total Male Cost', compute='compute_total_cost', store=True)
    total_female_cost = fields.Float(string='Total female Cost', compute='compute_total_cost', store=True)
    actual_male_cost = fields.Float(string='Actual Male Cost', )
    actual_female_cost = fields.Float(string='Actual female Cost', )

    real_consumption_ids = fields.One2many('real.consumption', 'chick_production_id', string="Real Consumption")

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ], default='draft', string='State')

    @api.depends('real_consumption_ids')
    def compute_total_cost(self):
        for record in self:
            record.total_male_cost = sum(line.cost for line in record.real_consumption_ids.filtered(lambda l: l.gender == 'male'))
            record.total_female_cost = sum(line.cost for line in record.real_consumption_ids.filtered(lambda l: l.gender == 'female'))
            record.total_cost = sum(line.cost for line in record.real_consumption_ids)

    @api.depends('total_male_cost', 'male_quantity')
    def compute_unitary_male_cost(self):
        for record in self:
            record.male_unitary_cost = record.total_male_cost / record.male_quantity

    @api.depends('total_male_cost', 'male_quantity')
    def compute_unitary_male_cost(self):
        for record in self:
            record.male_unitary_cost = record.total_male_cost / record.male_quantity

    @api.depends('start_date', 'phase_id')
    def _compute_estimated_end_date(self):
        for record in self:
            if record.start_date and record.phase_id.duration:
                record.estimated_end_date = record.start_date + timedelta(days=record.phase_id.duration)

    # @api.depends('import_folder')
    # def _compute_reception_date(self):
    #     for record in self:
    #         record.reception_date = max(record.import_folder.mapped('reception_date'), default=False)

    @api.depends('male_quantity', 'female_quantity')
    def _compute_remaining_quantities(self):
        for record in self:
            record.quantity_male_remaining = record.male_quantity - self._get_male_losses(record)
            record.quantity_female_remaining = record.female_quantity - self._get_female_losses(record)

    @api.depends('male_quantity', 'female_quantity')
    def _compute_mortality_rates(self):
        for record in self:
            record.male_mortality_rate = (
                self._get_male_losses(record) / record.male_quantity * 100 if record.male_quantity else 0
            )
            record.female_mortality_rate = (
                self._get_female_losses(record) / record.female_quantity * 100 if record.female_quantity else 0
            )

    @api.depends('day')
    def _compute_week(self):
        for record in self:
            record.week = (record.day // 7) + 1

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('chick.production') or 'CP/0000'
        return sequence

    def _get_male_losses(self, record):
        """Simulate male losses calculation."""
        return 0  # Replace with actual logic

    def _get_female_losses(self, record):
        """Simulate female losses calculation."""
        return 0  # Replace with actual logic

    def reset_to_draft(self):
        for record in self:
            if not record.total_cost:  # Replace with logic for checking consumption
                record.state = 'draft'


class RealConsumption(models.Model):
    _name = 'real.consumption'
    _description = 'Real Consumption'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity_per_unit = fields.Float(string="Quantity per Unit", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    total_quantity = fields.Float(string="Total Quantity")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        store=True,
        string="Tracking", related="product_id.tracking")
    cost = fields.Float(string="Cost", store=True, compute='_compute_cost')
    date = fields.Date(string="Date", default=fields.Date.context_today)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender Animal", required=True)

    is_confirmed = fields.Boolean(
        string='Is confirmed',
        required=False)

    product_category_id = fields.Many2one(
        comodel_name='uom.category',
        string='Category',
        store=True,
        related="product_id.uom_id.category_id",
        required=False)

    @api.onchange('quantity_per_unit', 'gender')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = record.quantity_per_unit * record.chick_production_id.female_quantity if record.gender == 'female' else record.quantity_per_unit * record.chick_production_id.male_quantity

    @api.onchange('product_id')
    def _onchange_product(self):
        for record in self:
            record.uom_id = record.product_id.uom_id.id

    @api.depends('total_quantity', 'product_id', 'uom_id')
    def _compute_cost(self):
        for record in self:
            if record.product_id and record.total_quantity > 0:
                product_cost = record.product_id.standard_price  # Standard price of the product
                uom_factor = record.uom_id._compute_quantity(1.0, record.product_id.uom_id)  # Conversion factor
                record.cost = product_cost * record.total_quantity * uom_factor
            else:
                record.cost = 0.0

    @api.onchange('total_quantity', 'product_id', 'uom_id', 'lot_id')
    def _verify_quantity(self):
        for record in self:
            if record.product_id and record.uom_id and record.total_quantity > 0:
                if round(self.env['stock.quant']._get_available_quantity(
                        record.product_id,
                        record.chick_production_id.building_id.stock_location_id
                ), 2) < record.total_quantity:
                    raise ValidationError(_("Quantité non disponible !"))

                if record.product_id.tracking == 'lot' and record.lot_id:
                    if round(self.env['stock.quant']._get_available_quantity(
                            record.product_id,
                            record.chick_production_id.building_id.stock_location_id,
                            lot_id=record.lot_id,
                    ), 2) < record.total_quantity:
                        raise ValidationError(_("Quantité non disponible !"))

    def action_confirm_consumption(self):
        location_production = self.env['stock.location'].search([('usage', '=', 'production')])
        for record in self:
            pick_output = self.env['stock.picking'].create({
                # 'name': 'Soins',
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_id': record.chick_production_id.building_id.stock_location_id.id,
                'location_dest_id': location_production.id,
                'origin': record.chick_production_id.name,
                'move_ids': [(0, 0, {
                    'name': record.product_id.name,
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.total_quantity,
                    'product_uom': record.uom_id.id,
                    'location_id': record.chick_production_id.building_id.stock_location_id.id,
                    'location_dest_id': location_production.id,
                    'quantity': record.total_quantity,
                    'move_line_ids': [(0, 0, {
                        'product_id': record.product_id.id,
                        'product_uom_id': record.uom_id.id,
                        'quantity': record.total_quantity,
                        'location_id': record.chick_production_id.building_id.stock_location_id.id,
                        'location_dest_id': location_production.id,
                        'lot_id': record.lot_id.id if record.lot_id else False,
                    })]
                })],
            })
            pick_output.button_validate()
            record.is_confirmed = True
