from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    chick_production_id = fields.Many2one('chick.production', string='Production')


