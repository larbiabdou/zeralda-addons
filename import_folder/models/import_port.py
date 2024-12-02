from odoo import api, fields, models


class ImportPort(models.Model):
    _name = 'import.port'
    _description = 'Import Port'

    name = fields.Char()

