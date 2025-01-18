from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rc = fields.Char(
        string='RC',
        required=False)
    nif = fields.Char(
        string='NIF',
        required=False)
    ai = fields.Char(
        string='AI',
        required=False)
    nis = fields.Char(
        string='NIS',
        required=False)
