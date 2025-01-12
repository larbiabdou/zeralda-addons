from odoo import models, fields, api, _
from datetime import timedelta, date

from odoo.exceptions import ValidationError


class ChickProduction(models.Model):
    _name = 'chick.production'
    _description = 'Chick Production'

    # Basic fields
    name = fields.Char(string='Name', required=True, default='/' )
    start_date = fields.Date(string='Start Date', required=True)
    phase_id = fields.Many2one('production.phase', string='Phase', required=True)
    estimated_end_date = fields.Date(string='Estimated End Date', compute='_compute_estimated_end_date', store=True)
    previous_production_id = fields.Many2one(
        comodel_name='chick.production',
        string='Previous production',
        required=False)
    next_production_id = fields.Many2one(
        comodel_name='chick.production',
        string='Next production',
        required=False)
    end_date = fields.Date(
        string='End date',
        required=False)
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=False)
    # Import Folder and Reception Details
    import_folder = fields.Many2one('import.folder', string='Import Folder')
    reception_date = fields.Date(string='Reception Date', store=True)

    # Male and Female Quantities and Costs
    male_quantity = fields.Float(string='Male Quantity', compute="compute_male_quantities", store=True)
    male_unitary_cost = fields.Float(string='Male Unitary Cost', compute="compute_unitary_male_cost", store=True)
    female_quantity = fields.Float(string='female Quantity', compute="compute_female_quantities", store=True)
    female_unitary_cost = fields.Float(string='female Unitary Cost', compute="compute_unitary_female_cost", store=True)
    eggs_quantity = fields.Integer(
        string='Eggs quantity',
        compute="compute_eggs_quantity", store=True,
        required=False)
    # Remaining Quantities
    quantity_male_remaining = fields.Float(string='Quantity Male Remaining', compute='_compute_remaining_quantities', store=True)
    quantity_female_remaining = fields.Float(string='Quantity female Remaining', compute='_compute_remaining_quantities', store=True)

    # Mortality Rates
    male_mortality_rate = fields.Float(string='Male Mortality Rate (%)', compute='_compute_mortality_rates', store=True)
    female_mortality_rate = fields.Float(string='female Mortality Rate (%)', compute='_compute_mortality_rates', store=True)

    # Building and Day/Week
    building_id = fields.Many2one('chicken.building', string='Building')
    day = fields.Integer(string='Day', compute="_compute_day")
    week = fields.Integer(string='Week', compute='_compute_day')

    # Costs
    total_cost = fields.Float(string='Total Cost', compute='compute_total_cost', store=True)
    total_male_cost = fields.Float(string='Total Male Cost', compute='compute_total_cost', store=True)
    total_female_cost = fields.Float(string='Total female Cost', compute='compute_total_cost', store=True)
    actual_male_cost = fields.Float(string='Actual Male Cost', compute="compute_actual_male_cost")
    actual_female_cost = fields.Float(string='Actual female Cost', compute="compute_actual_female_cost")
    unitary_eggs_cost = fields.Float(
        string='Eggs unitary cost',
        compute="compute_unitary_eggs_cost",
        required=False)
    real_consumption_ids = fields.One2many('real.consumption', 'chick_production_id', string="Real Consumption")
    weight_record_ids = fields.One2many('weight.record', 'chick_production_id', string="Weight Records")
    product_declaration_ids = fields.One2many(
        comodel_name='product.declaration',
        inverse_name='chick_production_id',
        string='Declarations',
        domain=[('type', '=', 'declaration')],
        required=False)
    product_loss_ids = fields.One2many(
        comodel_name='product.declaration',
        inverse_name='chick_production_id',
        string='Loss',
        domain=[('type', '=', 'loss')],
        required=False)
    product_component_ids = fields.One2many(
        comodel_name='product.declaration',
        inverse_name='chick_production_id',
        string='Components',
        domain=[('type', '=', 'raw')],
        required=False)
    equipment_ids = fields.One2many(
        'chick.production.equipment',
        'production_id',
        string='Équipements'
    )

    cost_ids = fields.One2many(
        comodel_name='chick.production.cost',
        inverse_name='chick_production_id',
        string='Costs',
        required=False)

    type = fields.Selection(
        string='Type',
        related='phase_id.type',
        store=True,
        required=False, )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ], default='draft', string='State')

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Équipement',
        required=True
    )
    capacity = fields.Integer(
        string='Capacity',
        related='equipment_id.capacity',
        required=False)

    free_quantity = fields.Integer(
        string='Free Quantity',
        compute="compute_free_quantity",
        required=False)

    def compute_free_quantity(self):
        for record in self:
            record.free_quantity = record.capacity - record.eggs_quantity

    def open_previous_production(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Production',
            'res_model': 'chick.production',
            'view_mode': 'form',
            'res_id': self.previous_production_id.id
        }

    def open_next_production(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Production',
            'res_model': 'chick.production',
            'view_mode': 'form',
            'res_id': self.next_production_id.id
        }

    def unlink(self):
        for production in self:
            if production.state != 'draft':  # Adjust 'confirmed' to match your actual confirmed state
                raise ValidationError(_('You cannot delete a confirmed production'))
        return super(ChickProduction, self).unlink()

    @api.depends('product_component_ids', 'product_component_ids.quantity')
    def compute_eggs_quantity(self):
        for record in self:
            record.eggs_quantity = 0
            record.eggs_quantity = sum(line.quantity for line in record.product_component_ids.filtered(lambda l: l.product_id.is_eggs))

    @api.depends('product_component_ids')
    def compute_male_quantities(self):
        for record in self:
            record.male_quantity = 0
            record.male_quantity = sum(line.quantity for line in record.product_component_ids.filtered(lambda l: l.product_id.gender == 'male'))

    @api.depends('product_component_ids')
    def compute_female_quantities(self):
        for record in self:
            record.female_quantity = 0
            record.female_quantity = sum(line.quantity for line in record.product_component_ids.filtered(lambda l: l.product_id.gender == 'female'))

    def action_open_next_phase_wizard(self):
        if self.phase_id.next_phase_id and self.phase_id.next_phase_id.type == 'eggs_production':
            domain_lot_ids = self.product_declaration_ids.filtered(lambda l:l.product_id.gender == 'female').mapped('lot_id')
            domain_product_ids = self.phase_id.declare_product_ids.filtered(lambda l:l.gender == 'female')
        else:
            domain_lot_ids = self.product_declaration_ids.mapped('lot_id')
            domain_product_ids = self.phase_id.declare_product_ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Next Phase',
            'res_model': 'chick.production.next.phase.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_domain_product_ids': domain_product_ids.ids,
                'default_next_phase_id': self.phase_id.next_phase_id.id,
                'default_domain_lot_ids': domain_lot_ids.ids,
                'default_building_id': self.building_id.id,
            }
        }

    def open_incubation_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incubation wizard',
            'res_model': 'incubation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_chick_production_id': self.id,
            }
        }

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
            if record.phase_id.type == 'phase_1':
                male_reception_cost = sum(line.value for line in record.import_folder.purchase_order_ids.picking_ids.move_ids.stock_valuation_layer_ids.filtered(
                    lambda l: l.product_id.gender == 'male'))
                male_quantity = record.import_folder.purchase_order_ids.picking_ids.move_ids.filtered(
                    lambda l: l.product_id.gender == 'male')[0].quantity
                male_reception_cost = male_reception_cost / male_quantity * record.quantity_male_remaining
                female_reception_cost = sum(line.value for line in record.import_folder.purchase_order_ids.picking_ids.move_ids.stock_valuation_layer_ids.filtered(
                    lambda l: l.product_id.gender == 'female'))
                female_quantity = record.import_folder.purchase_order_ids.picking_ids.move_ids.filtered(
                    lambda l: l.product_id.gender == 'female')[0].quantity
                female_reception_cost = female_reception_cost / female_quantity * record.quantity_female_remaining
            elif record.phase_id.type == 'incubation':
                eggs_reception_cost = sum(line.unit_cost * line.quantity for line in record.product_component_ids)
            else:
                male_reception_cost = record.previous_production_id.male_unitary_cost * record.quantity_male_remaining
                female_reception_cost = record.previous_production_id.female_unitary_cost * record.quantity_female_remaining
            if record.phase_id.type == 'incubation':
                equipment_cost = record.equipment_id.cost_per_unit * record.eggs_quantity
                if eggs_reception_cost > 0:
                    self.env['chick.production.cost'].create({
                        'name': 'Eggs reception cost',
                        'chick_production_id': record.id,
                        'type': 'reception',
                        #'gender': 'male',
                        'amount': eggs_reception_cost,
                    })
                if equipment_cost > 0:
                    self.env['chick.production.cost'].create({
                        'name': _('Incubator cost'),
                        'chick_production_id': record.id,
                        'type': 'equipment',
                        'amount': equipment_cost,
                    })
            else:
                if record.quantity_male_remaining > 0:
                    self.env['chick.production.cost'].create({
                        'name': 'Male reception cost',
                        'chick_production_id': record.id,
                        'type': 'reception',
                        'gender': 'male',
                        'amount': male_reception_cost ,
                    })
                if record.quantity_female_remaining > 0:
                    self.env['chick.production.cost'].create({
                        'name': 'Female reception cost',
                        'chick_production_id': record.id,
                        'type': 'reception',
                        'gender': 'female',
                        'amount': female_reception_cost,
                    })

    def action_start_progress(self):
        for record in self:
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            record.state = 'completed'
            if not record.end_date:
                record.end_date = date.today()

    def action_cancel(self):
        for record in self:
            record.state = 'canceled'

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def action_loss(self):
        domain_lot_ids = self.product_component_ids.mapped('lot_id')
        return {
            'name': _('Produce'),
            'type': 'ir.actions.act_window',
            'res_model': 'produce.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_chick_production_id': self.id,
                'default_type': 'loss',
                'default_domain_lot_ids': domain_lot_ids.ids,
                'default_domain_consumed_product_ids': self.product_component_ids.mapped('product_id').ids,
            },
        }

    def action_produce(self):
        domain_lot_ids = self.product_component_ids.mapped('lot_id')
        return {
            'name': _('Produce'),
            'type': 'ir.actions.act_window',
            'res_model': 'produce.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_chick_production_id': self.id,
                'default_type': 'declaration',
                'default_domain_lot_ids': domain_lot_ids.ids,
                'default_domain_product_ids': self.phase_id.declare_product_ids.ids,
                'default_domain_consumed_product_ids': self.product_component_ids.mapped('product_id').ids,
                'building_id': self.building_id.id,
            },
        }

    @api.depends('cost_ids')
    def compute_total_cost(self):
        for record in self:
            record.total_male_cost = sum(line.amount for line in record.cost_ids.filtered(lambda l: l.gender == 'male'))
            record.total_female_cost = sum(line.amount for line in record.cost_ids.filtered(lambda l: l.gender == 'female'))
            record.total_cost = sum(line.amount for line in record.cost_ids)

    @api.depends('total_male_cost', 'quantity_male_remaining')
    def compute_unitary_male_cost(self):
        for record in self:
            record.male_unitary_cost = record.total_male_cost / record.quantity_male_remaining if record.quantity_male_remaining != 0 else 0

    @api.depends('total_cost', 'eggs_quantity')
    def compute_unitary_eggs_cost(self):
        for record in self:
            record.unitary_eggs_cost = record.total_cost / record.eggs_quantity if record.eggs_quantity != 0 else 0

    @api.depends('total_female_cost', 'quantity_female_remaining')
    def compute_unitary_female_cost(self):
        for record in self:
            record.female_unitary_cost = record.total_female_cost / record.quantity_female_remaining if record.quantity_female_remaining != 0 else 0

    @api.depends('start_date', 'phase_id', 'phase_id.duration')
    def _compute_estimated_end_date(self):
        for record in self:
            if record.start_date and record.phase_id.duration:
                record.estimated_end_date = record.start_date + timedelta(days=record.phase_id.duration)

    # @api.onchange('import_folder')
    # def onchange_import_folder(self):
    #     for record in self:
    #         if record.import_folder:
    #             record.male_quantity = sum(line.quantity for line in record.import_folder.purchase_order_ids.picking_ids.move_ids.filtered(
    #                 lambda l: l.product_id.gender == 'male'))
    #             record.female_quantity = sum(line.quantity for line in record.import_folder.purchase_order_ids.picking_ids.move_ids.filtered(
    #                 lambda l: l.product_id.gender == 'female'))

    @api.depends('male_quantity', 'female_quantity', 'product_loss_ids')
    def _compute_remaining_quantities(self):
        for record in self:
            record.quantity_male_remaining = record.male_quantity - record._get_male_losses()
            record.quantity_female_remaining = record.female_quantity - record._get_female_losses()

    def _get_male_declarations(self):
        return sum(line.quantity for line in self.product_declaration_ids.filtered(lambda l: l.gender == 'male'))

    def _get_female_declarations(self):
        return sum(line.quantity for line in self.product_declaration_ids.filtered(lambda l: l.gender == 'female'))

    @api.depends('male_quantity', 'female_quantity', 'product_loss_ids')
    def _compute_mortality_rates(self):
        for record in self:
            record.male_mortality_rate = (
                self._get_male_losses() / record.male_quantity * 100 if record.male_quantity else 0
            )
            record.female_mortality_rate = (
                self._get_female_losses() / record.female_quantity * 100 if record.female_quantity else 0
            )

    def _compute_day(self):
        for record in self:
            if record.start_date:
                today = date.today()
                delta = today - record.start_date
                record.day = delta.days
                record.week = (record.day // 7) + 1
            else:
                record.day = 0
                record.week = 0


    # def _generate_name(self):
    #     sequence = self.env['ir.sequence'].next_by_code('chick.production') or 'CP/0000'
    #     return sequence

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('chick.production') or _('New')
        return super(ChickProduction, self).create(vals)

    def _get_male_losses(self):
        return sum(line.quantity for line in self.product_loss_ids.filtered(lambda l: l.gender == 'male'))

    def _get_female_losses(self):
        return sum(line.quantity for line in self.product_loss_ids.filtered(lambda l: l.gender == 'female'))

    def reset_to_draft(self):
        for record in self:
            if not record.total_cost:  # Replace with logic for checking consumption
                record.state = 'draft'

    def open_consumptions(self):
        return {
            'name': 'Consumptions',
            'type': 'ir.actions.act_window',
            'res_model': 'real.consumption',
            'view_mode': 'tree,form',
            'context': {'default_chick_production_id': self.id},
            'domain': [('chick_production_id', '=', self.id)],
        }


class RealConsumption(models.Model):
    _name = 'real.consumption'
    _description = 'Real Consumption'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity_per_unit = fields.Float(string="Quantity per Unit", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related="product_id.uom_id",
        required=False)
    total_quantity = fields.Float(string="Total Quantity")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        store=True,
        string="Tracking", related="product_id.tracking")
    cost = fields.Float(string="Cost", store=True)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender Animal")

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
            if record.chick_production_id.type == 'eggs_production':
                gender = 'female'
            else:
                gender = record.gender
            quantity = record.uom_id._compute_quantity(record.quantity_per_unit, record.product_id.uom_id)
            record.total_quantity = quantity * record.chick_production_id.female_quantity if gender == 'female' else record.quantity_per_unit * record.chick_production_id.male_quantity

    @api.onchange('product_id')
    def _onchange_product(self):
        for record in self:
            record.uom_id = record.product_id.uom_id.id
    #
    # @api.depends('total_quantity', 'product_id', 'uom_id')
    # def _compute_cost(self):
    #     for record in self:
    #         if record.product_id and record.total_quantity > 0:
    #             product_cost = record.product_id.standard_price  # Standard price of the product
    #             uom_factor = record.uom_id._compute_quantity(1.0, record.product_id.uom_id)  # Conversion factor
    #             record.cost = product_cost * record.total_quantity * uom_factor
    #         else:
    #             record.cost = 0.0

    #@api.onchange('total_quantity', 'product_id', 'uom_id', 'lot_id')
    def _verify_quantity(self):
        for record in self:
            quantity = record.uom_id._compute_quantity(record.total_quantity, record.product_id.uom_id)
            if record.product_id and record.uom_id and quantity > 0:
                if round(self.env['stock.quant']._get_available_quantity(
                        record.product_id,
                        record.chick_production_id.building_id.stock_location_id
                ), 2) < quantity:
                    raise ValidationError(_("Quantité non disponible !"))

                if record.product_id.tracking == 'lot' and record.lot_id:
                    if round(self.env['stock.quant']._get_available_quantity(
                            record.product_id,
                            record.chick_production_id.building_id.stock_location_id,
                            lot_id=record.lot_id,
                    ), 2) < quantity:
                        raise ValidationError(_("Quantité non disponible !"))

    def unlink(self):
        for record in self:
            if record.is_confirmed:  # Adjust 'confirmed' to match your actual confirmed state
                raise ValidationError(_('You cannot delete a confirmed consumption line'))
        return super(RealConsumption, self).unlink()

    def action_confirm_consumption(self):
        location_production = self.env['stock.location'].search([('usage', '=', 'production')])
        for record in self:
            record._verify_quantity()
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
            record.cost = abs(sum(line.value for line in pick_output.move_ids.stock_valuation_layer_ids.filtered(
                lambda l: l.product_id == record.product_id)))
            record.is_confirmed = True
            if record.chick_production_id.type == 'eggs_production':
                gender = 'female'
            else:
                gender = record.gender
            self.env['chick.production.cost'].create({
                'name': record.product_id.name,
                'resource': record.product_id.name,
                'chick_production_id': record.chick_production_id.id,
                'type': 'input',
                'gender': gender,
                'amount': record.cost,
                'product_id': record.product_id.id,
                'date': record.date,
            })

class WeightRecord(models.Model):
    _name = 'weight.record'
    _description = 'Weight Record'

    chick_production_id = fields.Many2one('chick.production', string="Chick Production", ondelete='cascade')
    gender_animal = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender Animal", required=True)
    initial_weight = fields.Float(string="Initial Weight")
    average_current_weight = fields.Float(string="Average Current Weight")
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)

from odoo import models, fields, api

class ChickProductionEquipment(models.Model):
    _name = 'chick.production.equipment'
    _description = 'Équipements utilisés dans la production'

    production_id = fields.Many2one('chick.production', string='Production', required=True, ondelete='cascade')
    equipment_id = fields.Many2one('maintenance.equipment', string='Équipement', required=True)
    duration = fields.Float(string='Durée', required=True)
    uom_id = fields.Many2one(
        'uom.uom',
        string='UdM',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_wtime').id)],
        required=True
    )
    date = fields.Date(string='Date', required=True)
    cost = fields.Float(string='Coût', compute='_compute_cost', store=True)
    is_confirmed = fields.Boolean(
        string='Is_confirmed',
        required=False)

    @api.depends('equipment_id', 'duration')
    def _compute_cost(self):
        for record in self:
            if record.equipment_id and record.duration and record.equipment_id.uom_id:
                cost = record.equipment_id.cost  # Standard price of the product
                uom_factor = record.uom_id._compute_quantity(1.0, record.equipment_id.uom_id)  # Conversion factor
                record.cost = cost * record.duration * uom_factor
            else:
                record.cost = 0.0

    def button_confirm(self):
        for record in self:
            if record.production_id.type != 'eggs_production':
                self.env['chick.production.cost'].create({
                    'name': record.equipment_id.name,
                    'resource': record.equipment_id.name,
                    'chick_production_id': record.production_id.id,
                    'type': 'equipment',
                    'amount': record.cost * record.production_id.quantity_male_remaining / (record.production_id.quantity_male_remaining + record.production_id.quantity_female_remaining),
                    'gender': 'male',
                    'equipment_id': record.equipment_id.id,
                    'date': record.date,
                })
            self.env['chick.production.cost'].create({
                'name': record.equipment_id.name,
                'resource': record.equipment_id.name,
                'chick_production_id': record.production_id.id,
                'type': 'equipment',
                'amount': record.cost * record.production_id.quantity_female_remaining / (record.production_id.quantity_male_remaining + record.production_id.quantity_female_remaining),
                'gender': 'female',
                'equipment_id': record.equipment_id.id,
                'date': record.date,
            })
            record.is_confirmed = True

