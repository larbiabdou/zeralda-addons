from odoo import models, fields, api

class ChickConfiguration(models.Model):
    _name = 'chick.configuration'
    _description = 'Chick Configuration'

    tracking_type = fields.Selection([
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity')
    ], string="Type of Tracking", required=True)

    day_range = fields.Integer(string="Day Range", required=True)
    end_range = fields.Integer(string="End Range", required=True)

    min_target_temperature = fields.Float(
        string="Min Target Temperature",
        required=False,
        help="Minimum target temperature",
        default=0.0
    )
    max_target_temperature = fields.Float(
        string="Max Target Temperature",
        required=False,
        help="Maximum target temperature",
        default=0.0
    )
    min_target_humidity = fields.Float(
        string="Min Target Humidity",
        required=False,
        help="Minimum target humidity",
        default=0.0
    )
    max_target_humidity = fields.Float(
        string="Max Target Humidity",
        required=False,
        help="Maximum target humidity",
        default=0.0
    )

    @api.onchange('tracking_type')
    def _onchange_tracking_type(self):
        if self.tracking_type == 'temperature':
            self.min_target_humidity = 0.0
            self.max_target_humidity = 0.0
        elif self.tracking_type == 'humidity':
            self.min_target_temperature = 0.0
            self.max_target_temperature = 0.0
