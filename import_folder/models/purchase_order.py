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

