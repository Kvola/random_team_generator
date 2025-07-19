from odoo import models, fields, api
import random
from odoo.exceptions import ValidationError  # <-- Cet import est crucial

class RandomTask(models.Model):
    _name = 'random.task'
    _description = 'Random Task'

    name = fields.Char(string='Nom de la tâche', required=True)
    description = fields.Text(string='Description')

class Team(models.Model):
    _name = 'random.team'
    _description = 'Team'

    name = fields.Char(string='Nom équipe', required=True)
    members_ids = fields.Many2many('res.partner', string='Membres')
    team_lead_id = fields.Many2one('res.partner', string='Responsable')
    team_lead_phone = fields.Char(string='Téléphone (Responsable)', related='team_lead_id.phone', readonly=True, store=True)
    task_ids = fields.Many2many('random.task', string='Tâches')
    description = fields.Text(string='Description', compute='_compute_description', store=True)

    # Décrire les tâches liées à l'équipe
    @api.depends('task_ids')
    def _compute_description(self):
        """Compute the description based on the tasks assigned to the team."""
        for team in self:
            if team.task_ids:
                task_descriptions = ', '.join(task.description for task in team.task_ids)
                team.description = f'{task_descriptions}' if task_descriptions else 'Aucune tâche assignée.'
            

    # Champs pour identifier le type d'équipe et l'organisation parent
    team_type = fields.Selection([
        ('company', 'Équipe Compagnie'),
        ('tribe', 'Équipe Tribu'),
        ('prayer_cell', 'Équipe Cellule de prière'),
        ('group', 'Équipe Groupe'),
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

    @api.depends('team_type', 'company_id', 'tribe_id', 'prayer_cell_id', 'group_id')
    def _compute_members_domain(self):
        """Calcule le domaine pour les membres disponibles selon le type d'équipe et l'organisation."""
        for team in self:
            organization_id = team._get_organization_id(team)
            
            # Domaine de base : exclure les entreprises
            domain = [('is_company', '=', False)]
            
            if organization_id and team.team_type:
                # Trouver les membres déjà assignés à d'autres équipes du même type dans la même organisation
                existing_teams = self.env['random.team'].search([
                    ('id', '!=', team.id if team.id else False),
                    ('team_type', '=', team.team_type if team.team_type else False),
                ])
                
                # Filtrer par organisation et récupérer les membres déjà assignés
                assigned_member_ids = []
                for existing_team in existing_teams:
                    existing_org_id = team._get_organization_id(existing_team)
                    if existing_org_id == organization_id:
                        assigned_member_ids.extend(existing_team.members_ids.ids)
                
                # Exclure les membres déjà assignés
                if assigned_member_ids:
                    domain.append(('id', 'not in', assigned_member_ids))
                
                # Ajouter un filtre d'organisation si nécessaire selon le type d'équipe
                if team.team_type == 'company' and team.company_id:
                    # Pour les équipes company, on peut filtrer par church_id si nécessaire
                    pass
                elif team.team_type == 'tribe' and team.tribe_id:
                    # Pour les équipes tribu, filtrer par tribe_id si le champ existe sur res.partner
                    domain.append(('tribe_id', '=', team.tribe_id.id))
                elif team.team_type == 'prayer_cell' and team.prayer_cell_id:
                    # Pour les équipes cellule de prière
                    domain.append(('prayer_cell_id', '=', team.prayer_cell_id.id))
                elif team.team_type == 'group' and team.group_id:
                    # Pour les équipes groupe
                    domain.append(('group_id', '=', team.group_id.id))
            
            team.members_domain = str(domain)

    members_domain = fields.Char(compute='_compute_members_domain', store=False)

    @api.constrains('members_ids', 'team_type', 'company_id', 'tribe_id', 'prayer_cell_id', 'group_id')
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

    @api.model
    def create(self, vals):
        """Surcharge create pour s'assurer que l'organisation appropriée est définie."""
        team = super().create(vals)
        if not team._get_organization_id(team):
            # Si aucune organisation n'est définie, essaie de la déduire depuis les membres
            if team.members_ids:
                member = team.members_ids[0]
                if team.team_type == 'company':
                    team.company_id = member.church_id.id if member.church_id else False
                elif team.team_type == 'tribe':
                    team.tribe_id = member.tribe_id.id if member.tribe_id else False
                elif team.team_type == 'prayer_cell':
                    team.prayer_cell_id = member.prayer_cell_id.id if member.prayer_cell_id else False
                elif team.team_type == 'group':
                    team.group_id = member.group_id.id if member.group_id else False
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