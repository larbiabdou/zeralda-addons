from odoo import api, fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    import_folder_id = fields.Many2one(
        comodel_name='import.folder',
        string='Import_folder_id',
        required=False)

    def button_validate(self):
        res = super().button_validate()
        for record in self:
            if record.import_folder_id:
                record.import_folder_id.compute_landed_cost_matrix()
        return res

    def _get_targeted_move_ids(self):
        return self.picking_ids.move_ids.filtered(lambda l: l.product_id.gender != 'male')
