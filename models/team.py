from odoo import models, fields, api
import random

class Team(models.Model):
    _name = 'random.team'
    _description = 'Team'

    name = fields.Char(string='Nom équipe', required=True)
    members_ids = fields.Many2many('res.partner', string='Membres')
    team_lead_id = fields.Many2one('res.partner', string='Responsable')
    team_lead_phone = fields.Char(string='Téléphone (Responsable)', related='team_lead_id.phone', readonly=True, store=True)
    
    # Champs pour identifier le type d'équipe et l'organisation parent
    team_type = fields.Selection([
        ('company', 'Équipe Compagnie'),
        ('tribe', 'Équipe Tribu'),
        ('prayer_cell', 'Équipe Cellule de prière'),
        ('group', 'Équipe Groupe'),
        ('academy', 'Équipe Académie'),
    ], string='Type d\'équipe', required=True, default='company')
    
    # Relations vers les organisations
    company_id = fields.Many2one('res.partner', string='Compagnie', 
                                domain=[('is_company', '=', True), ('organization_type', 'in', [False, 'company'])])
    tribe_id = fields.Many2one('res.partner', string='Tribu', 
                              domain=[('organization_type', '=', 'tribe')])
    prayer_cell_id = fields.Many2one('res.partner', string='Cellule de prière', 
                                   domain=[('organization_type', '=', 'prayer_cell')])
    group_id = fields.Many2one('res.partner', string='Groupe', 
                              domain=[('organization_type', '=', 'group')])
    academy_id = fields.Many2one('res.partner', string='Académie', 
                                domain=[('organization_type', '=', 'academy')])

    @api.constrains('members_ids', 'team_type', 'company_id', 'tribe_id', 'prayer_cell_id', 'group_id', 'academy_id')
    def _check_unique_member_per_organization_team(self):
        """Vérifie qu'un membre ne fait partie que d'une seule équipe par type d'organisation."""
        for team in self:
            organization_id = self._get_organization_id(team)
            if not organization_id:
                continue
                
            for member in team.members_ids:
                # Cherche si ce membre est déjà dans une autre équipe du même type et de la même organisation
                existing_teams = self.env['random.team'].search([
                    ('id', '!=', team.id),
                    ('team_type', '=', team.team_type),
                    ('members_ids', 'in', member.id)
                ])
                
                # Filtre les équipes qui appartiennent à la même organisation
                for existing_team in existing_teams:
                    existing_org_id = self._get_organization_id(existing_team)
                    if existing_org_id == organization_id:
                        raise models.ValidationError(
                            f"Le contact '{member.name}' fait déjà partie d'une équipe "
                            f"de type '{dict(team._fields['team_type'].selection)[team.team_type]}' "
                            f"dans cette organisation."
                        )

    def _get_organization_id(self, team):
        """Retourne l'ID de l'organisation selon le type d'équipe."""
        if team.team_type == 'company':
            return team.company_id.id
        elif team.team_type == 'tribe':
            return team.tribe_id.id
        elif team.team_type == 'prayer_cell':
            return team.prayer_cell_id.id
        elif team.team_type == 'group':
            return team.group_id.id
        elif team.team_type == 'academy':
            return team.academy_id.id
        return False

    @api.onchange('team_type')
    def _onchange_team_type(self):
        """Réinitialise les champs d'organisation quand le type change."""
        if self.team_type != 'company':
            self.company_id = False
        if self.team_type != 'tribe':
            self.tribe_id = False
        if self.team_type != 'prayer_cell':
            self.prayer_cell_id = False
        if self.team_type != 'group':
            self.group_id = False
        if self.team_type != 'academy':
            self.academy_id = False

    @api.model
    def create(self, vals):
        """Surcharge create pour s'assurer que l'organisation appropriée est définie."""
        team = super().create(vals)
        if not team._get_organization_id(team):
            # Si aucune organisation n'est définie, essaie de la déduire depuis les membres
            if team.members_ids:
                member = team.members_ids[0]
                if team.team_type == 'company':
                    team.company_id = member.parent_id.id if member.parent_id else False
                elif team.team_type == 'tribe':
                    team.tribe_id = member.tribe_id.id if member.tribe_id else False
                elif team.team_type == 'prayer_cell':
                    team.prayer_cell_id = member.prayer_cell_id.id if member.prayer_cell_id else False
                elif team.team_type == 'group':
                    team.group_id = member.group_id.id if member.group_id else False
                elif team.team_type == 'academy':
                    team.academy_id = member.academy_id.id if member.academy_id else False
        return team

    def name_get(self):
        """Personnalise l'affichage du nom pour inclure l'organisation."""
        result = []
        for team in self:
            name = team.name
            organization_name = ""
            
            if team.team_type == 'company' and team.company_id:
                organization_name = f" ({team.company_id.name})"
            elif team.team_type == 'tribe' and team.tribe_id:
                organization_name = f" ({team.tribe_id.name})"
            elif team.team_type == 'prayer_cell' and team.prayer_cell_id:
                organization_name = f" ({team.prayer_cell_id.name})"
            elif team.team_type == 'group' and team.group_id:
                organization_name = f" ({team.group_id.name})"
            elif team.team_type == 'academy' and team.academy_id:
                organization_name = f" ({team.academy_id.name})"
            
            result.append((team.id, name + organization_name))
        return result

    def action_view_members(self):
        """Action pour afficher les membres de l'équipe."""
        return {
            'name': f'Membres de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.members_ids.ids)],
            'context': {'default_is_company': False}
        }