from odoo import api, fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    import_folder_id = fields.Many2one(
        comodel_name='import.folder',
        string='Import_folder_id',
        required=False)

