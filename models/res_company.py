from odoo import models, fields, api
import random

class ResCompany(models.Model):
    _description = 'Company'
    _inherit = 'res.company'

    @api.model
    def generate_random_teams(self):
        """Génère des équipes aléatoires en utilisant le paramètre de taille."""
        team_size = int(self.env['ir.config_parameter'].sudo().get_param('random_team.team_size', default=3))
        all_members = self.env['res.partner'].search([('is_company','=',False)])
        # Récupère tous les partenaires
        member_list = list(all_members)
        random.shuffle(member_list)
        # Mélange les membres
        teams = []
        # Suppression des équipes existantes pour simplifier l'exemple
        self.env['random.team'].search([]).unlink()
        for i in range(0, len(member_list), team_size):
            team_members = member_list[i:i + team_size]
            if team_members:
                team_name = f'Équipe n° {len(teams) + 1}'
                team_lead = random.choice(team_members)
                # Sélectionne un chef d'équipe
                team = self.env['random.team'].create({
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
        