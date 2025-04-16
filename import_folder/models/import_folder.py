from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ImportFolder(models.Model):
    _name = "import.folder"
    _description = "Import Folder"

    name = fields.Char(string="Folder Name", required=True)
    reference = fields.Char(string="Reference")
    comment = fields.Text(string="Comment")
    port_of_embarkation = fields.Many2one('import.port', string="Port of Embarkation")
    shipping_company = fields.Char(string="Shipping Company")
    opening_date = fields.Date(string="Opening Date")
    #reception_ids = fields.Many2many('stock.picking', string="Reception Reference", related="purchase_order_ids.picking_ids", store=True)
    etd = fields.Date(string="Estimated Time of Departure (ETD)")
    eta = fields.Date(string="Estimated Time of Arrival (ETA)")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    ], string="state", default='draft')

    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='import_folder_id',
        string='Purchase_order_ids',
        required=False)

    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='import_folder_id',
        string='Invoices',
        required=False)

    landed_costs_ids = fields.One2many(
        comodel_name='stock.landed.cost',
        inverse_name='import_folder_id',
        string='Landed_cost_ids',
        required=False)

    landed_costs_visible = fields.Boolean(
        string=' landed_costs_visible',
        compute="_compute_landed_costs_visible",
        required=False)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
    required = False)

    matrix_ids = fields.Many2many(
        comodel_name='landed.cost.matrix',
        string='Matrix')

    count_reception = fields.Integer(
        string=' count_reception',
        compute="compute_count_reception",
        required=False)

    count_purchases = fields.Integer(
        string='Count_purchases',
        compute="compute_count_purchases",
        required=False)

    count_douane_invoice = fields.Integer(
        string='Count_douane_invoice',
        compute="compute_count_douane_invoice",
        required=False)
    count_transit_invoice = fields.Integer(
        string='Count_douane_invoice',
        compute="compute_count_transit_invoice",
        required=False)
    count_local_invoice = fields.Integer(
        string='Count_douane_invoice',
        compute="compute_count_local_invoice",
        required=False)
    count_strange_invoice = fields.Integer(
        string='Count_douane_invoice',
        compute="compute_count_strange_invoice",
        required=False)
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("You can not delete a confirmed folder"))
        return super().unlink()

    def button_confirm(self):
        for record in self:
            record.state = 'in_progress'

    def action_view_landed_costs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        domain = [('id', 'in', self.landed_costs_ids.ids)]
        context = dict(self.env.context, default_import_folder_id=self.id)
        views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree2').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)

    def compute_count_reception(self):
        for record in self:
            record.count_reception = len(record.purchase_order_ids.picking_ids)

    def compute_count_purchases(self):
        for record in self:
            record.count_purchases = len(record.purchase_order_ids)

    def action_view_receptions(self):
        return {
            'name': 'Receptions',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'domain': [('id', 'in', self.purchase_order_ids.picking_ids.ids)],
        }

    def action_view_purchases(self):
        return {
            'name': 'Purchases',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
        }
    def compute_count_douane_invoice(self):
        for record in self:
            record.count_douane_invoice = self.env['account.move'].search_count([('import_type', '=', 'douane'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)])
    def compute_count_transit_invoice(self):
        for record in self:
            record.count_transit_invoice = self.env['account.move'].search_count([('import_type', '=', 'transit'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)])
    def compute_count_local_invoice(self):
        for record in self:
            record.count_local_invoice = self.env['account.move'].search_count([('import_type', '=', 'local'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)])
    def compute_count_strange_invoice(self):
        for record in self:
            record.count_strange_invoice = self.env['account.move'].search_count([('import_type', '=', 'strange'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)])
    def open_invoice_transit(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'transit',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'transit'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)],
        }
    def open_invoice_douane(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'douane',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'douane'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)],
        }
    def open_invoice_local(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'local',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'local'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)],
        }
    def open_invoice_strange(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'domain': [('import_type', '=', 'strange'),
                       ('is_import_folder', '=', True),
                       ('import_folder_id', '=', self.id)],
        }
    @api.depends('purchase_order_ids', 'purchase_order_ids.picking_ids', 'invoice_ids', 'invoice_ids.line_ids', 'invoice_ids.line_ids.is_landed_costs_line')
    def _compute_landed_costs_visible(self):
        for record in self:
            if record.landed_costs_ids:
                record.landed_costs_visible = False
            else:
                record.landed_costs_visible = any(line.is_landed_costs_line for line in record.invoice_ids.line_ids) and any(picking for picking in record.purchase_order_ids.picking_ids)

    def button_create_landed_costs(self):
        for record in self:
            """Create a `stock.landed.cost` record associated to the account move of `self`, each
            `stock.landed.costs` lines mirroring the current `account.move.line` of self.
            """
            self.ensure_one()
            landed_costs_lines = self.invoice_ids.line_ids.filtered(lambda line: line.is_landed_costs_line)

            landed_costs = self.env['stock.landed.cost'].with_company(self.company_id).create({
                'import_folder_id': record.id,
                'picking_ids': record.purchase_order_ids.picking_ids.ids,
                'cost_lines': [(0, 0, {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                    'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.invoice_date or fields.Date.context_today(l)),
                    'split_method': l.product_id.split_method_landed_cost or 'equal',
                }) for l in landed_costs_lines],
            })
            #if landed_costs:
                #landed_costs.button_validate()
                #record.compute_landed_cost_matrix()
            #record.state = 'closed'

    def action_close(self):
        for record in self:
            record.write({'state': 'closed'})

    def action_reopen(self):
        for record in self:
            record.write({'state': 'in_progress'})
        return True

    def compute_landed_cost_matrix(self):
        for record in self:
            record.matrix_ids = [(5, 0, 0)]
            data = []
            for landed_cost in record.landed_costs_ids:
                products = landed_cost.valuation_adjustment_lines.mapped('product_id')
                for product in products:
                    lines = landed_cost.valuation_adjustment_lines.filtered(lambda l: l.product_id == product)
                    purchase_line = record.purchase_order_ids.order_line.filtered(lambda l: l.product_id == product)
                    data.append([0, 0, {
                        'product_name': product.name,
                        'value': lines[0].quantity,
                        'title': _('Quantity')
                    }])
                    if purchase_line:
                        unit_price = purchase_line[0].price_unit
                        data.append([0, 0, {
                            'product_name': product.name,
                            'value': unit_price,
                            'title': _('Purchase price in %s' % purchase_line[0].currency_id.name)
                        }])
                    data.append([0, 0, {
                        'product_name': product.name,
                        'value': lines[0].former_cost / lines[0].quantity,
                        'title': _('Converted price in %s' % lines[0].currency_id.name)
                    }])
                    total_cost = 0
                    for line in lines:
                        total_cost += (line.additional_landed_cost / lines[0].quantity)
                    data.append([0, 0, {
                        'product_name': product.name,
                        'value': total_cost,
                        'title': _('Total Cost in %s' % line[0].currency_id.name)
                    }])
                    final_cost = (lines[0].former_cost / lines[0].quantity) + total_cost
                    data.append([0, 0, {
                        'product_name': product.name,
                        'value': final_cost,
                        'title': _('Final cost in %s' % line[0].currency_id.name)
                    }])
            record.matrix_ids = data

class LandedCostMatrix(models.Model):
    _name = 'landed.cost.matrix'
    _description = 'Landed Cost Matrix'

    product_name = fields.Char(
        string='Product_name',
        required=False)

    value = fields.Float(
        string='Value',
        required=False)

    title = fields.Char(
        string='Title',
        required=False)



