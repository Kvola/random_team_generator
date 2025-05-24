from odoo import models, fields, api
import random

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Types d'organisation
    organization_type = fields.Selection([
        ('company', 'Compagnie'),
        ('prayer_cell', 'Cellule de prière'),
        ('group', 'Groupe'),
        ('academy', 'Académie'),
    ], string='Type d\'organisation', default='company')

    # Relations spécialisées
    prayer_cell_id = fields.Many2one('res.partner', string='Cellule de prière', 
                                   domain=[('organization_type', '=', 'prayer_cell')])
    group_id = fields.Many2one('res.partner', string='Groupe', 
                              domain=[('organization_type', '=', 'group')])
    academy_id = fields.Many2one('res.partner', string='Académie', 
                                domain=[('organization_type', '=', 'academy')])

    # Membres par type d'organisation
    prayer_cell_members = fields.One2many('res.partner', 'prayer_cell_id', 
                                         string='Membres de la cellule')
    group_members = fields.One2many('res.partner', 'group_id', 
                                   string='Membres du groupe')
    academy_members = fields.One2many('res.partner', 'academy_id', 
                                     string='Membres de l\'académie')
    company_contacts = fields.One2many('res.partner', 'parent_id', 
                                      string='Contacts de l\'entreprise')

    # Compteurs pour boutons intelligents
    team_count = fields.Integer(string='Nombre d\'équipes', compute='_compute_team_count')
    prayer_cell_count = fields.Integer(string='Nombre de cellules', compute='_compute_prayer_cell_count')
    group_count = fields.Integer(string='Nombre de groupes', compute='_compute_group_count')
    academy_count = fields.Integer(string='Nombre d\'académies', compute='_compute_academy_count')

    @api.depends()
    def _compute_team_count(self):
        """Calcule le nombre d'équipes selon le type d'organisation."""
        for record in self:
            if record.is_company or record.organization_type in ['prayer_cell', 'group', 'academy']:
                domain = self._get_team_domain(record)
                teams = self.env['random.team'].search(domain)
                record.team_count = len(teams)
            else:
                record.team_count = 0

    @api.depends()
    def _compute_prayer_cell_count(self):
        """Calcule le nombre de cellules de prière."""
        for record in self:
            if record.is_company:
                cells = self.env['res.partner'].search([
                    ('organization_type', '=', 'prayer_cell'),
                    ('parent_id', '=', record.id)
                ])
                record.prayer_cell_count = len(cells)
            else:
                record.prayer_cell_count = 0

    @api.depends()
    def _compute_group_count(self):
        """Calcule le nombre de groupes."""
        for record in self:
            if record.is_company:
                groups = self.env['res.partner'].search([
                    ('organization_type', '=', 'group'),
                    ('parent_id', '=', record.id)
                ])
                record.group_count = len(groups)
            else:
                record.group_count = 0

    @api.depends()
    def _compute_academy_count(self):
        """Calcule le nombre d'académies."""
        for record in self:
            if record.is_company:
                academies = self.env['res.partner'].search([
                    ('organization_type', '=', 'academy'),
                    ('parent_id', '=', record.id)
                ])
                record.academy_count = len(academies)
            else:
                record.academy_count = 0

    def _get_team_domain(self, organization):
        """Retourne le domaine pour chercher les équipes selon le type d'organisation."""
        if organization.organization_type == 'prayer_cell':
            return [('members_ids.prayer_cell_id', '=', organization.id)]
        elif organization.organization_type == 'group':
            return [('members_ids.group_id', '=', organization.id)]
        elif organization.organization_type == 'academy':
            return [('members_ids.academy_id', '=', organization.id)]
        else:  # company
            return [('members_ids.parent_id', '=', organization.id)]

    def _get_members_by_type(self, organization_type, organization_id):
        """Retourne les membres selon le type d'organisation."""
        if organization_type == 'prayer_cell':
            return self.env['res.partner'].search([
                ('prayer_cell_id', '=', organization_id),
                ('is_company', '=', False)
            ])
        elif organization_type == 'group':
            return self.env['res.partner'].search([
                ('group_id', '=', organization_id),
                ('is_company', '=', False)
            ])
        elif organization_type == 'academy':
            return self.env['res.partner'].search([
                ('academy_id', '=', organization_id),
                ('is_company', '=', False)
            ])
        else:  # company
            return self.env['res.partner'].search([
                ('parent_id', '=', organization_id),
                ('is_company', '=', False)
            ])

    @api.model
    def generate_random_teams(self, organization_id, organization_type='company'):
        """Génère des équipes aléatoires pour une organisation."""
        team_size = int(self.env['ir.config_parameter'].sudo().get_param('random_team.team_size', default=3))
        
        # Récupère tous les membres de l'organisation
        members = self._get_members_by_type(organization_type, organization_id)
        
        if not members:
            return []
        
        member_list = list(members)
        random.shuffle(member_list)
        
        teams = []
        
        # Supprime les équipes existantes pour cette organisation
        organization = self.env['res.partner'].browse(organization_id)
        domain = self._get_team_domain(organization)
        existing_teams = self.env['random.team'].search(domain)
        existing_teams.unlink()
        
        # Détermine le préfixe du nom d'équipe selon le type
        type_names = {
            'company': 'Équipe',
            'prayer_cell': 'Équipe Cellule',
            'group': 'Équipe Groupe',
            'academy': 'Équipe Académie'
        }
        team_prefix = type_names.get(organization_type, 'Équipe')
        
        for i in range(0, len(member_list), team_size):
            team_members = member_list[i:i + team_size]
            if team_members:
                team_name = f'{team_prefix} n° {len(teams) + 1}'
                team_lead = random.choice(team_members)
                
                team = self.env['random.team'].create({
                    'name': team_name,
                    'members_ids': [(6, 0, [member.id for member in team_members])],
                    'team_lead_id': team_lead.id
                })
                teams.append(team)
        
        return teams

    def action_generate_teams(self):
        """Action pour générer des équipes selon le type d'organisation."""
        if not (self.is_company or self.organization_type in ['prayer_cell', 'group', 'academy']):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': 'Cette action n\'est disponible que pour les organisations.',
                    'type': 'warning'
                }
            }
        
        org_type = self.organization_type if not self.is_company else 'company'
        teams = self.generate_random_teams(self.id, org_type)
        
        if not teams:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': 'Aucun membre trouvé pour cette organisation.',
                    'type': 'info'
                }
            }
        
        # Recalcule le compteur d'équipes
        self._compute_team_count()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': f'{len(teams)} équipe(s) générée(s) avec succès !',
                'type': 'success'
            }
        }

    def action_view_teams(self):
        """Action pour afficher les équipes de cette organisation."""
        if not (self.is_company or self.organization_type in ['prayer_cell', 'group', 'academy']):
            return False
        
        domain = self._get_team_domain(self)
        teams = self.env['random.team'].search(domain)
        
        return {
            'name': f'Équipes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'random.team',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', teams.ids)],
            'context': {'default_organization_id': self.id}
        }

    # Actions pour afficher les différents types d'organisations
    def action_view_prayer_cells(self):
        """Action pour afficher les cellules de prière."""
        return {
            'name': f'Cellules de prière de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('organization_type', '=', 'prayer_cell'), ('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id, 'default_organization_type': 'prayer_cell', 'default_is_company': True}
        }

    def action_view_groups(self):
        """Action pour afficher les groupes."""
        return {
            'name': f'Groupes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('organization_type', '=', 'group'), ('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id, 'default_organization_type': 'group', 'default_is_company': True}
        }

    def action_view_academies(self):
        """Action pour afficher les académies."""
        return {
            'name': f'Académies de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('organization_type', '=', 'academy'), ('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id, 'default_organization_type': 'academy', 'default_is_company': True}
        }