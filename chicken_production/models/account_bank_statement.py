from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=False)



