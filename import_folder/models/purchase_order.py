from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    import_folder_id = fields.Many2one(
        comodel_name='import.folder',
        string='Import folder',
        required=False)

    is_import_folder = fields.Boolean(
        string='Is import folder',
        required=False)

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['is_import_folder'] = self.is_import_folder
        if self.import_folder_id:
            invoice_vals['import_folder_id'] = self.import_folder_id.id
            invoice_vals['import_type'] = 'strange'
        return invoice_vals

