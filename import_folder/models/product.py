from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_animal = fields.Boolean(
        string='Is animal',
        required=False)

    gender = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'),
                   ('female', 'Female'), ],
        required=False, )

    is_eggs = fields.Boolean(
        string='Is eggs',
        required=False)



