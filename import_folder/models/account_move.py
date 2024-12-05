from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    import_folder_id = fields.Many2one(
        comodel_name='import.folder',
        # related="purchase_id.import_folder_id",
        string='Import folder',
        required=False)

    is_import_folder = fields.Boolean(
        string='Is import folder',
        required=False)

    import_type = fields.Selection(
        string='Type',
        selection=[('transit', 'F.Transitaire'),
                   ('douane', 'F.Douane'),
                   ('local', 'F.Local'), ('strange', 'F.Etrangère')],
        required=False, )

    def open_invoice_transit(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'transit',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.import_folder_id.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'transit'),
                       ('is_import_folder', '=', self.is_import_folder),
                       ('import_folder_id', '=', self.import_folder_id.id)],
        }
    def open_invoice_douane(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'douane',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.import_folder_id.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'douane'),
                       ('is_import_folder', '=', self.is_import_folder),
                       ('import_folder_id', '=', self.import_folder_id.id)],
        }
    def open_invoice_local(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'context': {'default_import_type': 'local',
                        'default_is_import_folder': True,
                        'default_import_folder_id': self.import_folder_id.id,
                        'default_move_type': 'in_invoice'},
            'domain': [('import_type', '=', 'local'),
                       ('is_import_folder', '=', self.is_import_folder),
                       ('import_folder_id', '=', self.import_folder_id.id)],
        }
