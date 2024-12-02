from odoo import models, fields, api


class ImportFolder(models.Model):
    _name = "import.folder"
    _description = "Import Folder"

    name = fields.Char(string="Folder Name", required=True)
    reference = fields.Char(string="Reference")
    comment = fields.Text(string="Comment")
    port_of_embarkation = fields.Many2one('import.port', string="Port of Embarkation")
    shipping_company = fields.Char(string="Shipping Company")
    opening_date = fields.Date(string="Opening Date")
    purchase_order_reference = fields.Many2many('purchase.order', string="Purchase Order Reference")
    reception_reference = fields.Many2many('stock.picking', string="Reception Reference")
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

    def action_view_landed_costs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        domain = [('id', 'in', self.landed_costs_ids.ids)]
        context = dict(self.env.context, default_import_folder_id=self.id)
        views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree2').id, 'tree'), (False, 'form'), (False, 'kanban')]
        return dict(action, domain=domain, context=context, views=views)

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
            action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
            return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])
