from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    team_size = fields.Integer(
        string='Team Size',
        default=3,
        config_parameter='random_team.team_size',
        help="Default number of members in a team when generating random teams."
    )
