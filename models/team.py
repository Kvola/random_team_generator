from odoo import models, fields, api
import random

class Team(models.Model):
    _name = 'random.team'
    _description = 'Team'

    name = fields.Char(string='Nom équipe', required=True)
    members_ids = fields.Many2many('res.partner', string='Membres')
    team_lead_id = fields.Many2one('res.partner', string='Responsable')
    team_lead_phone = fields.Char(string='Téléphone (Responsable)', related='team_lead_id.phone', readonly=True, store=True)
    # Dans votre modèle
    TEAM_COLORS = [
        ('red', 'Rouge - Équipe Alpha'),
        ('blue', 'Bleu - Équipe Beta'), 
        ('green', 'Vert - Équipe Gamma'),
        ('orange', 'Orange - Équipe Delta'),
        ('purple', 'Violet - Équipe Epsilon'),
    ]
    color = fields.Selection(TEAM_COLORS, default='blue')

    @api.model
    def generate_random_teams(self):
        """Génère des équipes aléatoires en utilisant le paramètre de taille."""
        team_size = int(self.env['ir.config_parameter'].sudo().get_param('random_team.team_size', default=3))
        all_members = self.env['res.partner'].search([('is_company','=',False)])  # Récupère tous les partenaires
        member_list = list(all_members)
        random.shuffle(member_list)  # Mélange les membres
        teams = []

        # Suppression des équipes existantes pour simplifier l'exemple
        self.search([]).unlink()

        for i in range(0, len(member_list), team_size):
            team_members = member_list[i:i + team_size]
            if team_members:
                team_name = f'Équipe n° {len(teams) + 1}'
                team_lead = random.choice(team_members)  # Sélectionne un chef d'équipe
                team = self.create({
                    'name': team_name,
                    'members_ids': [(6, 0, [member.id for member in team_members])],
                    'team_lead_id': team_lead.id
                })
                teams.append(team)
        return teams

    def action_generate_teams(self):
        """Action liée au bouton pour générer des équipes."""
        self.generate_random_teams()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  # Recharge la vue pour afficher les nouvelles équipes
        }
