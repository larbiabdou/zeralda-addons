from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    import_folder_id = fields.Many2one(
        comodel_name='import.folder',
        #related="purchase_id.import_folder_id",
        string='Import folder',
        required=False)

    is_import_folder = fields.Boolean(
        string='Is import folder',
        required=False)

    invoice_import_type = fields.Selection(
        string='Type',
        selection=[('transport', 'Transport'),
                   ('dédouanement', 'Dédouanement'),
                   ('transitaire', 'Transitaire')],
        required=False, )
