from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

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
