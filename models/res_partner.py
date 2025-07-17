from odoo import models, fields, api
from datetime import datetime, timedelta, date
import random

class RandomTribe(models.Model):
    _name = 'random.tribe'
    _description = 'Tribu'

    name = fields.Char(string='Nom de la tribu', required=True)
    description = fields.Text(string='Description')
class RandomPrayerCell(models.Model):
    _name = 'random.prayer.cell'
    _description = 'Cellule de prière'

    name = fields.Char(string='Nom de la cellule de prière', required=True)
    description = fields.Text(string='Description')
    tribe_id = fields.Many2one('random.tribe', string='Tribu associée',
                               help="Tribu à laquelle cette cellule de prière est associée")
# Extension du modèle res.partner pour la gestion des équipes et informations personnelles
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Types d'organisation
    organization_type = fields.Selection([
        ('company', 'Église'),
        ('tribe', 'Tribu'),
        ('prayer_cell', 'Cellule de prière'),
        ('group', 'Groupe'),
        ('academy', 'Autre Structure'),
        ('region', 'Région'),
    ], string='Type d\'organisation', default='company')
    
    # Relations spécialisées
    # église de la tribu
    tribe_church_id = fields.Many2one('res.partner', string='Église de la tribu',
                                 domain=[('organization_type', '=', 'company')])
    # tribu de la cellule de prière
    prayer_cell_tribe_id = fields.Many2one('res.partner', string='Tribu de la cellule',
                        domain=[('organization_type', '=', 'tribe')])
    # église de la cellule de prière
    prayer_cell_church_id = fields.Many2one('res.partner', string='Église de la cellule', 
                            related='prayer_cell_tribe_id.tribe_church_id', store=True, readonly=True)
    # église du groupe d'âge
    group_church_id = fields.Many2one('res.partner', string='Église du groupe',
                                 domain=[('organization_type', '=', 'company')])
    # église de la structure
    academy_church_id = fields.Many2one('res.partner', string='Église de la structure',
                                 domain=[('organization_type', '=', 'company')])

    prayer_cell_type_id = fields.Many2one('random.prayer.cell', string='Type de cellule de prière',
                                       domain="[('id', '!=', False)]",
                                       help="Type de cellule de prière pour cette organisation")
    tribe_type_id = fields.Many2one('random.tribe', string='Type de tribu',
                                 domain="[('id', '!=', False)]",
                                 help="Type de tribu pour cette organisation")

    # église du fidèle
    church_id = fields.Many2one('res.partner', string='Église',
                                 domain=[('organization_type', '=', 'company')])
    # tribu du fidèle
    tribe_id = fields.Many2one('res.partner', string='Tribu',
                             domain=[('organization_type', '=', 'tribe'),('tribe_church_id', '=', church_id)])
    # cellule de prière du fidèle
    prayer_cell_id = fields.Many2one('res.partner', string='Cellule de prière', 
                    domain=[('organization_type', '=', 'prayer_cell'), ('prayer_cell_church_id', '=', church_id)])
    # groupe d'âge du fidèle
    group_id = fields.Many2one('res.partner', string='Groupe', 
                              domain=[('organization_type', '=', 'group'), ('group_church_id', '=', church_id)])
    # autre structure du fidèle
    academy_id = fields.Many2one('res.partner', string='Autre Structure', 
                                domain=[('organization_type', '=', 'academy'), ('academy_church_id', '=', church_id)])

    region_id = fields.Many2one('res.partner', string='Région',
                                 domain=[('organization_type', '=', 'region')])
    regional_capital_id = fields.Many2one('res.partner', string='Chef-lieu de région',
                                        domain="[('organization_type', '=', 'company'), ('region_id', '=', id)]")
    regional_pastor_id = fields.Many2one('res.partner', string='Pasteur régional', related='regional_capital_id.main_pastor_id', store=True)

    # ========== NOUVELLES INFORMATIONS PERSONNELLES ==========

    # Sexe
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
    ], string='Sexe')
    
    # Date de naissance et âge
    birthdate = fields.Date(string='Date de naissance')
    age = fields.Integer(string='Âge', compute='_compute_age', store=True)
    
    # Situation matrimoniale
    marital_status = fields.Selection([
        ('single', 'Célibataire'),
        ('married', 'Marié(e)'),
        ('divorced', 'Divorcé(e)'),
        ('widowed', 'Veuf/Veuve'),
        ('separated', 'Séparé(e)'),
        ('cohabiting', 'Concubinage'),
    ], string='Situation matrimoniale', default='single')
    
    # Conjoint
    spouse_id = fields.Many2one('res.partner', string='Conjoint(e)', 
                               domain="[('is_company', '=', False), ('id', '!=', id)]")
    
    # Enfants
    
    father_id = fields.Many2one('res.partner', string='Père', domain=[('gender', '=', 'male'), ('is_company', '=', False)])
    mother_id = fields.Many2one('res.partner', string='Mère', domain=[('gender', '=', 'female'), ('is_company', '=', False)])
    children_from_father_ids = fields.One2many(
        'res.partner',
        inverse_name='father_id',
        string='Enfants (père)',
        domain="[('father_id', '=', id)]"
    )
    children_from_mother_ids = fields.One2many(
        'res.partner',
        inverse_name='mother_id',
        string='Enfants (mère)',
        domain="[('mother_id', '=', id)]"
    )

    @api.constrains('father_id', 'mother_id')
    def _check_parents_different(self):
        for record in self:
            if record.father_id and record.mother_id and record.father_id == record.mother_id:
                raise ValidationError("Le père et la mère doivent être deux personnes différentes.")
    
    # Compteur d'enfants
    mother_children_count = fields.Integer(string='Nombre d\'enfants de la mère', compute='_compute_mother_children_count')
    father_children_count = fields.Integer(string='Nombre d\'enfants du père', compute='_compute_father_children_count')

    # Date de salut et statut nouveau
    arrival_date = fields.Date(string='Date de salut', default=fields.Date.context_today)
    is_new_member = fields.Boolean(string='Nouveau membre', compute='_compute_is_new_member', store=False)
    
    # ========== FIN NOUVELLES INFORMATIONS ==========

    # Membres par type d'organisation
    prayer_cell_members = fields.One2many('res.partner', 'prayer_cell_id', 
                                         string='Membres de la cellule')
    group_members = fields.One2many('res.partner', 'group_id', 
                                   string='Membres du groupe')
    academy_members = fields.One2many('res.partner', 'academy_id', 
                                     string='Membres de la structure')
    tribe_members = fields.One2many('res.partner', 'tribe_id',
                                   string='Membres de la tribu')
    company_contacts = fields.One2many('res.partner', 'church_id', 
                                      string='Membres de l\'église')

    # Champs calculés pour afficher les équipes de chaque type
    company_team_ids = fields.Many2many('random.team', compute='_compute_team_memberships', 
                                       string='Équipes Compagnie')
    tribe_team_ids = fields.Many2many('random.team', compute='_compute_team_memberships', 
                                     string='Équipes Tribu')
    prayer_cell_team_ids = fields.Many2many('random.team', compute='_compute_team_memberships', 
                                           string='Équipes Cellule')
    group_team_ids = fields.Many2many('random.team', compute='_compute_team_memberships', 
                                     string='Équipes Groupe')
    academy_team_ids = fields.Many2many('random.team', compute='_compute_team_memberships', 
                                       string='Équipes Structure')
    
    # Compteurs pour les boutons intelligents (organisations)
    team_count = fields.Integer(string='Nombre d\'équipes', compute='_compute_organization_counts')
    tribe_count = fields.Integer(string='Nombre de tribus', compute='_compute_organization_counts')
    prayer_cell_count = fields.Integer(string='Nombre de cellules', compute='_compute_organization_counts')
    group_count = fields.Integer(string='Nombre de groupes', compute='_compute_organization_counts')
    academy_count = fields.Integer(string='Nombre de structures', compute='_compute_organization_counts')
    
    # Compteurs pour les boutons intelligents (contacts individuels)
    total_teams_count = fields.Integer(string='Total équipes', compute='_compute_team_counts')
    company_teams_count = fields.Integer(string='Équipes Compagnie', compute='_compute_team_counts')
    tribe_teams_count = fields.Integer(string='Équipes Tribu', compute='_compute_team_counts')
    prayer_cell_teams_count = fields.Integer(string='Équipes Cellule', compute='_compute_team_counts')
    group_teams_count = fields.Integer(string='Équipes Groupe', compute='_compute_team_counts')
    academy_teams_count = fields.Integer(string='Équipes Structure', compute='_compute_team_counts')

    # Tranches d'âge pour les groupes
    min_age = fields.Integer(
        string="Âge minimum",
        help="Âge minimum pour ce groupe",
        invisible=lambda self: not self._is_age_group(),
    )
    max_age = fields.Integer(
        string="Âge maximum",
        help="Âge maximum pour ce groupe",
        invisible=lambda self: not self._is_age_group(),
    )

    # Dans la classe ResPartner(models.Model)

    # Champ pour stocker si c'est l'anniversaire aujourd'hui
    is_birthday = fields.Boolean(string="Anniversaire aujourd'hui", compute='_compute_is_birthday', store=False)
    
    # Champ pour suivre si l'alerte a déjà été envoyée aujourd'hui
    birthday_alert_sent = fields.Boolean(string="Alerte anniversaire envoyée", default=False)

    # Critères de sexe pour les groupes
    required_gender = fields.Selection([
        ('male', 'Hommes seulement'),
        ('female', 'Femmes seulement'),
        ('mixed', 'Mixte (hommes et femmes)'),
    ], string='Sexe requis', 
    default='mixed',
    invisible=lambda self: not self._is_age_group(),
    help="Définit si le groupe est réservé aux hommes, aux femmes ou mixte")

    # Critère de situation matrimoniale pour les groupes
    marital_requirement = fields.Selection([
        ('any', 'Toutes situations'),
        ('married_only', 'Mariés seulement'),
        ('single_only', 'Célibataires seulement'),
    ], string='Situation matrimoniale requise', 
    default='any',
    invisible=lambda self: not self._is_age_group(),
    help="Définit si le groupe accepte seulement les personnes mariées, seulement les célibataires ou toutes situations")

    # Pour les églises
    is_church = fields.Boolean(string="Est une église")
    is_in_a_church = fields.Boolean(string="Est dans une église", 
    related='church_id.is_church',
    readonly=True,
    store=True
    )
    main_pastor_id = fields.Many2one('res.partner', string="Pasteur principal",
                                domain="[('is_pastor','=',True), ('church_id','=',id)]")
    # Pour les pasteurs adjoints
    assistant_pastor_ids = fields.Many2many(
        'res.partner', 
        'church_assistant_pastor_rel',  # Nom explicite de la table de relation
        'church_id', 
        'pastor_id',
        string="Pasteurs adjoints",
        domain="[('is_pastor','=',True), ('church_id','=',id)]"
    )
    parent_church_id = fields.Many2one('res.partner', string="Église mère",
                                    domain="[('is_church','=',True)]")

    # Pour les membres
    is_pastor = fields.Boolean(string="Pasteur")
    is_elder = fields.Boolean(string="Ancien")
    is_deacon = fields.Boolean(string="Diacre")
    is_missionary = fields.Boolean(string="Missionnaire")
    is_leader = fields.Boolean(string="Responsable")
    is_pastor_wife = fields.Boolean(string="Femme de pasteur")
    church_id = fields.Many2one('res.partner', string="Église",
                            domain="[('is_church','=',True)]")

    # Responsables des organisations
    group_leader_id = fields.Many2one('res.partner', string="Responsable du groupe",
                                    domain="[('is_leader','=',True), ('group_id','=',id)]")
    # Pour les responsables adjoints de groupe
    group_assistant_leader_ids = fields.Many2many(
        'res.partner',
        'group_assistant_leader_rel',
        'group_id',
        'leader_id',
        string="Responsables adjoints du groupe",
        domain="[('is_leader','=',True), ('group_id','=',id)]"
    )

    prayer_cell_leader_id = fields.Many2one('res.partner', string="Responsable de la cellule",
                                        domain="[('is_leader','=',True), ('prayer_cell_id','=',id)]")
    # Pour les responsables adjoints de cellule
    prayer_cell_assistant_leader_ids = fields.Many2many(
        'res.partner',
        'cell_assistant_leader_rel',
        'cell_id',
        'leader_id',
        string="Responsables adjoints de la cellule",
        domain="[('is_leader','=',True), ('prayer_cell_id','=',id)]"
    )

    academy_leader_id = fields.Many2one('res.partner', string="Responsable de la structure",
                                    domain="[('is_leader','=',True), ('academy_id','=',id)]")
    # Pour les responsables adjoints de structure
    academy_assistant_leader_ids = fields.Many2many(
        'res.partner',
        'academy_assistant_leader_rel',
        'academy_id',
        'leader_id',
        string="Responsables adjoints de la structure",
        domain="[('is_leader','=',True), ('academy_id','=',id)]"
    )
    
    # Champ calculé pour compter les églises filles
    child_church_count = fields.Integer(string="Nombre d'églises filles", compute='_compute_child_church_count')
    regional_church_count = fields.Integer(string="Nombre d'églises régionales", compute='_compute_regional_church_count')
    def _compute_regional_church_count(self):
        """Calcule le nombre d'églises régionales associées à cette région."""
        for partner in self:
            if partner.organization_type == 'region':
                partner.regional_church_count = self.search_count([
                    ('region_id', '=', partner.id),
                    ('is_church', '=', True)
                ])
            else:
                partner.regional_church_count = 0
    
    def action_view_regional_churches(self):
        """Action pour voir les églises régionales associées à cette région."""
        self.ensure_one()
        if self.organization_type != 'region':
            return False
        return {
            'name': f'Églises régionales de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('region_id', '=', self.id), ('is_church', '=', True)],
            'context': {'default_region_id': self.id, 'default_is_church': True}
        }

    def action_validate_inscription(self):
        self.ensure_one()
        self.write({'active': True})
        # Envoyer un email de confirmation
        #template = self.env.ref('random_team_generator.email_template_inscription_validated')
        #template.send_mail(self.id, force_send=True)
        return True

    def action_archive(self):
        self.ensure_one()
        self.write({'active': False})
        return True

    def _compute_child_church_count(self):
        for partner in self:
            partner.child_church_count = self.search_count([
                ('parent_church_id', '=', partner.id),
                ('is_church', '=', True)
            ])

    # Action pour voir les églises filles
    def action_view_child_churches(self):
        self.ensure_one()
        return {
            'name': f'Églises filles de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('parent_church_id', '=', self.id), ('is_church', '=', True)],
            'context': {'default_parent_church_id': self.id, 'default_is_church': True}
        }

    # Contrainte pour la femme de pasteur
    @api.constrains('is_pastor_wife', 'spouse_id')
    def _check_pastor_wife(self):
        for partner in self:
            if partner.is_pastor_wife and (not partner.spouse_id or not partner.spouse_id.is_pastor):
                raise ValidationError("Une femme de pasteur doit avoir un conjoint qui est pasteur")

    # Mise à jour automatique quand on définit le conjoint
    @api.onchange('spouse_id')
    def _onchange_spouse_id(self):
        if self.gender == 'female' and self.spouse_id and self.spouse_id.is_pastor:
            self.is_pastor_wife = True
        elif self.gender == 'female' and not (self.spouse_id and self.spouse_id.is_pastor):
            self.is_pastor_wife = False

    @api.depends('birthdate')
    def _compute_is_birthday(self):
        """Détermine si c'est l'anniversaire du contact aujourd'hui."""
        today = date.today()
        for partner in self:
            if partner.birthdate:
                birthdate = fields.Date.from_string(partner.birthdate)
                partner.is_birthday = (birthdate.month == today.month and 
                                      birthdate.day == today.day)
            else:
                partner.is_birthday = False
    
    @api.model
    def _cron_check_birthdays(self):
        """Méthode appelée par le cron pour vérifier les anniversaires."""
        today = date.today()
        # Recherche tous les contacts dont c'est l'anniversaire aujourd'hui
        # et pour lesquels l'alerte n'a pas encore été envoyée
        birthday_contacts = self.search([
            ('birthdate', '!=', False),
            ('is_company', '=', False),
            ('birthday_alert_sent', '=', False),
            ('active', '=', True)
        ]).filtered(
            lambda p: fields.Date.from_string(p.birthdate).month == today.month and
                     fields.Date.from_string(p.birthdate).day == today.day
        )
        
        if birthday_contacts:
            # Envoie les notifications
            self._send_birthday_alerts(birthday_contacts)
            # Marque les alertes comme envoyées
            birthday_contacts.write({'birthday_alert_sent': True})
        
        # Réinitialise le flag pour les contacts dont ce n'est plus l'anniversaire
        yesterday = today - timedelta(days=1)
        self.search([
            ('birthday_alert_sent', '=', True),
            ('birthdate', '!=', False),
            ('active', '=', True)
        ]).filtered(
            lambda p: fields.Date.from_string(p.birthdate).month != today.month or
                     fields.Date.from_string(p.birthdate).day != today.day
        ).write({'birthday_alert_sent': False})
    
    def _send_birthday_alerts(self, contacts):
        """Envoie les notifications d'anniversaire."""
        for contact in contacts:
            # Crée une activité pour alerter les utilisateurs
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f"Anniversaire de {contact.name}",
                'note': f"Aujourd'hui c'est l'anniversaire de {contact.name} ({contact.age} ans). Pensez à lui souhaiter un bon anniversaire!",
                'user_id': self.env.user.id,
                'res_id': contact.id,
                'res_model_id': self.env['ir.model']._get('res.partner').id,
                'date_deadline': fields.Date.today(),
            })
            
            # Envoie une notification à tous les utilisateurs
            partner_ids = self.env['res.users'].search([]).mapped('partner_id').ids
            if partner_ids:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'body': f"🎉 Aujourd'hui c'est l'anniversaire de <b>{contact.name}</b> ({contact.age} ans). Pensez à lui souhaiter un bon anniversaire!",
                    'subject': f"Anniversaire de {contact.name}",
                    'partner_ids': [(6, 0, partner_ids)],
                    'model': 'res.partner',
                    'res_id': contact.id,
                })

    def _is_age_group(self):
        """Détermine si ce partenaire est un groupe avec tranche d'âge"""
        return self.is_company and self.organization_type == 'group'

    # ========== NOUVELLES MÉTHODES DE CALCUL ==========
    
    @api.depends('birthdate')
    def _compute_age(self):
        """Calcule l'âge à partir de la date de naissance."""
        today = date.today()
        for partner in self:
            if partner.birthdate:
                birthdate = fields.Date.from_string(partner.birthdate)
                age = today.year - birthdate.year
                if (today.month, today.day) < (birthdate.month, birthdate.day):
                    age -= 1
                partner.age = age
            else:
                partner.age = 0

    @api.depends('children_from_mother_ids')
    def _compute_mother_children_count(self):
        """Calcule le nombre d'enfants."""
        for partner in self:
            partner.mother_children_count = len(partner.children_from_mother_ids)

    @api.depends('children_from_father_ids')
    def _compute_father_children_count(self):
        """Calcule le nombre d'enfants."""
        for partner in self:
            partner.father_children_count = len(partner.children_from_father_ids)

    @api.depends('arrival_date')
    def _compute_is_new_member(self):
        """Détermine si le membre est nouveau selon la durée configurée"""
        duration = int(self.env['ir.config_parameter'].sudo().get_param('random_team_generator.new_member_duration', 30))
        for partner in self:
            if partner.arrival_date and not partner.is_company:
                today = fields.Date.context_today(self)
                limit_date = today - timedelta(days=duration)
                partner.is_new_member = partner.arrival_date > limit_date
            else:
                partner.is_new_member = False
    
    @api.onchange('birthdate')
    def _onchange_birthdate(self):
        """Met à jour l'âge et le groupe lorsque la date de naissance change."""
        if self.birthdate:
            self._compute_age()
            self._assign_age_group()
    
    def _assign_age_group(self):
        """Assigne automatiquement le groupe en fonction de l'âge, du sexe et de la situation matrimoniale."""
        if not self.is_company and self.age > 0:
            # Trouver le groupe approprié en fonction des critères
            domain = [
                ('is_company', '=', True),
                ('organization_type', '=', 'group'),
                ('min_age', '<=', self.age),
                ('max_age', '>=', self.age)
            ]
            
            # Ajouter les critères de sexe si définis
            if self.gender:
                # Recherche les groupes qui acceptent le sexe du membre ou qui sont mixtes
                domain += ['|',
                    ('required_gender', '=', 'mixed'),
                    ('required_gender', '=', self.gender)
                ]
            
            # Ajouter les critères de situation matrimoniale si définis
            if self.marital_status:
                # Recherche les groupes qui acceptent la situation du membre
                domain += ['|',
                    ('marital_requirement', '=', 'any'),
                    '|',
                    '&', ('marital_requirement', '=', 'married_only'), ('marital_status', '=', 'married'),
                    '&', ('marital_requirement', '=', 'single_only'), ('marital_status', 'in', ['single', 'divorced', 'widowed', 'separated', 'cohabiting'])
                ]
            
            age_group = self.env['res.partner'].search(domain, limit=1)
            
            if age_group:
                self.group_id = age_group.id
    
    # ========== CONTRAINTES ET VALIDATIONS ==========
    @api.constrains('required_gender', 'marital_requirement')
    def _check_group_requirements(self):
        """Vérifie que les critères du groupe sont cohérents."""
        for group in self.filtered(lambda r: r._is_age_group()):
            if group.required_gender not in ['male', 'female', 'mixed']:
                raise ValidationError("Le sexe requis doit être 'Hommes seulement', 'Femmes seulement' ou 'Mixte'")
            if group.marital_requirement not in ['any', 'married_only', 'single_only']:
                raise ValidationError("La situation matrimoniale requise doit être 'Toutes situations', 'Mariés seulement' ou 'Célibataires seulement'")

    @api.constrains('min_age', 'max_age')
    def _check_age_range(self):
        """Vérifie que la tranche d'âge est valide"""
        for group in self.filtered(lambda r: r._is_age_group()):
            if group.min_age < 0:
                raise ValidationError("L'âge minimum ne peut pas être négatif")
            if group.max_age < 0:
                raise ValidationError("L'âge maximum ne peut pas être négatif")
            if group.min_age > group.max_age:
                raise ValidationError("L'âge minimum ne peut pas être supérieur à l'âge maximum")
            if group.max_age > 120:
                raise ValidationError("L'âge maximum ne peut pas dépasser 120 ans")

    @api.constrains('spouse_id')
    def _check_spouse_reciprocity(self):
        """Vérifie que la relation de mariage est réciproque."""
        for partner in self:
            if partner.spouse_id and partner.spouse_id.spouse_id != partner:
                # Mise à jour automatique de la relation réciproque
                partner.spouse_id.spouse_id = partner
                if partner.spouse_id.marital_status != 'married':
                    partner.spouse_id.marital_status = 'married'
    
    @api.constrains('marital_status', 'spouse_id')
    def _check_marital_consistency(self):
        """Vérifie la cohérence entre le statut marital et le conjoint."""
        for partner in self:
            if partner.marital_status == 'married' and not partner.spouse_id:
                # On permet d'être marié sans avoir le conjoint renseigné
                pass
            elif partner.marital_status != 'married' and partner.spouse_id:
                # Si on a un conjoint mais qu'on n'est pas marié, on met à jour le statut
                partner.marital_status = 'married'
    
    @api.onchange('marital_status')
    def _onchange_marital_status(self):
        """Nettoie le champ conjoint si le statut n'est plus marié."""
        if self.marital_status != 'married':
            self.spouse_id = False
    
    # ========== ACTIONS POUR LES BOUTONS INTELLIGENTS ==========
    
    def action_view_children(self):
        if self.is_company:
            return False
        domain = ['|', ('father_id', '=', self.id), ('mother_id', '=', self.id)]
        return {
            'name': f'Enfants de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'default_father_id': self.id if self.gender == 'male' else False,
                'default_mother_id': self.id if self.gender == 'female' else False,
                'default_is_company': False
            }
        }
    
    def action_view_group_members_by_age(self):
        """Action pour afficher les membres du groupe filtrés par tranche d'âge, sexe et situation matrimoniale."""
        if not self.is_company or self.organization_type != 'group':
            return False
        
        # Construction du domaine de base avec l'âge
        domain = [
            ('is_company', '=', False),
            ('group_id', '=', self.id),
            ('age', '>=', self.min_age),
            ('age', '<=', self.max_age)
        ]
        
        # Ajout du critère de sexe si nécessaire
        if self.required_gender != 'mixed':
            domain.append(('gender', '=', self.required_gender))
        
        # Ajout du critère de situation matrimoniale si nécessaire
        if self.marital_requirement == 'married_only':
            domain.append(('marital_status', '=', 'married'))
        elif self.marital_requirement == 'single_only':
            domain.append(('marital_status', 'in', ['single', 'divorced', 'widowed', 'separated', 'cohabiting']))
        # Retourne l'action pour afficher les membres du groupe
        return {
            'name': f'Membres du groupe {self.name} (Âge: {self.min_age}-{self.max_age})',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_group_id': self.id}
        }
    
    # ========== MÉTHODES EXISTANTES ==========

    @api.depends()
    def _compute_organization_counts(self):
        """Calcule le nombre d'organisations enfants et d'équipes pour les organisations."""
        for partner in self:
            if partner.is_company:
                org_type = partner.organization_type if partner.organization_type else 'company'
                
                # Compte les équipes selon le type d'organisation
                teams = self._get_existing_teams(partner, org_type)
                partner.team_count = len(teams)
                
                # Compte les organisations enfants selon le type
                if org_type == 'company':
                    # Une compagnie peut avoir des tribus, groupes et structures
                    partner.tribe_count = self.env['res.partner'].search_count([
                        ('is_company', '=', True),
                        ('organization_type', '=', 'tribe'),
                        ('church_id', '=', partner.id)
                    ])
                    partner.group_count = self.env['res.partner'].search_count([
                        ('is_company', '=', True),
                        ('organization_type', '=', 'group'),
                        ('church_id', '=', partner.id)
                    ])
                    partner.academy_count = self.env['res.partner'].search_count([
                        ('is_company', '=', True),
                        ('organization_type', '=', 'academy'),
                        ('church_id', '=', partner.id)
                    ])
                    partner.prayer_cell_count = 0
                elif org_type == 'tribe':
                    # Une tribu peut avoir des cellules de prière
                    partner.prayer_cell_count = self.env['res.partner'].search_count([
                        ('is_company', '=', True),
                        ('organization_type', '=', 'prayer_cell'),
                        ('church_id', '=', partner.id)
                    ])
                    partner.tribe_count = 0
                    partner.group_count = 0
                    partner.academy_count = 0
                else:
                    # Autres types n'ont pas d'organisations enfants
                    partner.tribe_count = 0
                    partner.prayer_cell_count = 0
                    partner.group_count = 0
                    partner.academy_count = 0
            else:
                # Pour les contacts individuels, tous les compteurs d'organisations sont à 0
                partner.team_count = 0
                partner.tribe_count = 0
                partner.prayer_cell_count = 0
                partner.group_count = 0
                partner.academy_count = 0

    @api.depends()
    def _compute_team_memberships(self):
        """Calcule les équipes dont fait partie ce contact."""
        for partner in self:
            if partner.is_company:
                # Pour les organisations, on ne calcule pas les appartenances d'équipe
                partner.company_team_ids = False
                partner.tribe_team_ids = False
                partner.prayer_cell_team_ids = False
                partner.group_team_ids = False
                partner.academy_team_ids = False
            else:
                # Cherche toutes les équipes dont fait partie ce contact
                all_teams = self.env['random.team'].search([('members_ids', 'in', partner.id)])
                
                partner.company_team_ids = all_teams.filtered(lambda t: t.team_type == 'company')
                partner.tribe_team_ids = all_teams.filtered(lambda t: t.team_type == 'tribe')
                partner.prayer_cell_team_ids = all_teams.filtered(lambda t: t.team_type == 'prayer_cell')
                partner.group_team_ids = all_teams.filtered(lambda t: t.team_type == 'group')
                partner.academy_team_ids = all_teams.filtered(lambda t: t.team_type == 'academy')

    @api.depends()
    def _compute_team_counts(self):
        """Calcule le nombre d'équipes par type."""
        for partner in self:
            if partner.is_company:
                partner.company_teams_count = 0
                partner.tribe_teams_count = 0
                partner.prayer_cell_teams_count = 0
                partner.group_teams_count = 0
                partner.academy_teams_count = 0
                partner.total_teams_count = 0
            else:
                partner.company_teams_count = len(partner.company_team_ids)
                partner.tribe_teams_count = len(partner.tribe_team_ids)
                partner.prayer_cell_teams_count = len(partner.prayer_cell_team_ids)
                partner.group_teams_count = len(partner.group_team_ids)
                partner.academy_teams_count = len(partner.academy_team_ids)
                partner.total_teams_count = (partner.company_teams_count + 
                                           partner.tribe_teams_count + 
                                           partner.prayer_cell_teams_count + 
                                           partner.group_teams_count + 
                                           partner.academy_teams_count)

    def action_view_tribes(self):
        """Action pour afficher les tribus de cette compagnie."""
        if not self.is_company or (self.organization_type and self.organization_type != 'company'):
            return False
            
        tribes = self.env['res.partner'].search([
            ('is_company', '=', True),
            ('organization_type', '=', 'tribe'),
            ('church_id', '=', self.id)
        ])
        
        return {
            'name': f'Tribus de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', tribes.ids)],
        }

    def action_view_prayer_cells(self):
        """Action pour afficher les cellules de prière."""
        if not self.is_company:
            return False
            
        if (not self.organization_type or self.organization_type == 'company') or self.organization_type == 'tribe':
            prayer_cells = self.env['res.partner'].search([
                ('is_company', '=', True),
                ('organization_type', '=', 'prayer_cell'),
                ('church_id', '=', self.id)
            ])
            
            return {
                'name': f'Cellules de prière de {self.name}',
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', prayer_cells.ids)],
            }
        return False

    def action_view_groups(self):
        """Action pour afficher les groupes de cette compagnie."""
        if not self.is_company or (self.organization_type and self.organization_type != 'company'):
            return False
            
        groups = self.env['res.partner'].search([
            ('is_company', '=', True),
            ('organization_type', '=', 'group'),
            ('church_id', '=', self.id)
        ])
        
        return {
            'name': f'Groupes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', groups.ids)],
        }

    def action_view_academies(self):
        """Action pour afficher les structures de cette compagnie."""
        if not self.is_company or (self.organization_type and self.organization_type != 'company'):
            return False
            
        academies = self.env['res.partner'].search([
            ('is_company', '=', True),
            ('organization_type', '=', 'academy'),
            ('church_id', '=', self.id)
        ])
        
        return {
            'name': f'Structures de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', academies.ids)],
        }

    def action_view_my_teams(self):
        """Action pour afficher toutes les équipes de ce contact."""
        if self.is_company:
            return False
            
        all_teams = self.env['random.team'].search([('members_ids', 'in', self.id)])
        
        return {
            'name': f'Équipes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'random.team',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', all_teams.ids)],
        }

    def action_view_teams_by_type(self, team_type):
        """Action pour afficher les équipes d'un type spécifique."""
        if self.is_company:
            return False
            
        teams = self.env['random.team'].search([
            ('members_ids', 'in', self.id),
            ('team_type', '=', team_type)
        ])
        
        type_names = {
            'company': 'Compagnie',
            'tribe': 'Tribu',
            'prayer_cell': 'Cellule de prière',
            'group': 'Groupe',
            'academy': 'Structure'
        }
        
        return {
            'name': f"Équipes {type_names.get(team_type, '')} de {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'random.team',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', teams.ids)],
        }

    def debug_members(self):
        """Méthode de debug pour vérifier les membres d'une organisation."""
        if not self.is_company:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Debug',
                    'message': 'Cette méthode fonctionne uniquement sur les organisations (is_company=True)',
                    'type': 'warning'
                }
            }
        
        org_type = self.organization_type if self.organization_type else 'company'
        members = self._get_members_by_type(org_type, self.id)
        
        # Information de debug
        debug_info = []
        debug_info.append(f"Organisation: {self.name}")
        debug_info.append(f"Type: {org_type}")
        debug_info.append(f"ID: {self.id}")
        debug_info.append(f"Nombre de membres trouvés: {len(members)}")
        
        if org_type == 'tribe':
            # Info spécifique pour les tribus
            direct_members = self.env['res.partner'].search([
                ('is_company', '=', False),
                ('tribe_id', '=', self.id)
            ])
            prayer_cells = self.env['res.partner'].search([
                ('is_company', '=', True),
                ('organization_type', '=', 'prayer_cell'),
                ('church_id', '=', self.id)
            ])
            debug_info.append(f"Membres directs de la tribu: {len(direct_members)}")
            debug_info.append(f"Cellules de prière: {len(prayer_cells)}")
            
            for cell in prayer_cells:
                cell_members = self.env['res.partner'].search([
                    ('is_company', '=', False),
                    ('prayer_cell_id', '=', cell.id)
                ])
                debug_info.append(f"  - {cell.name}: {len(cell_members)} membres")
        
        if members:
            debug_info.append("Membres:")
            for member in members:
                debug_info.append(f"  - {member.name}")
        
        message = "\n".join(debug_info)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Debug - Membres de l\'organisation',
                'message': message,
                'type': 'info',
                'sticky': True
            }
        }

    def generate_random_teams(self):
        """Génère des équipes aléaoires pour cette organisation."""
        if not self.is_company:
            return False
            
        org_type = self.organization_type if self.organization_type else 'company'
        teams = self._generate_teams_for_organization(self.id, org_type)
        
        # Rafraîchit les compteurs
        self._compute_organization_counts()
        
        return {
            'name': f'Équipes générées pour {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'random.team',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [team.id for team in teams])],
        }

    @api.model
    def _generate_teams_for_organization(self, organization_id, organization_type='company'):
        """Génère des équipes aléaoires pour une organisation."""
        team_size = int(self.env['ir.config_parameter'].sudo().get_param('random_team_generator.team_size', default=3))
        
        # Récupère tous les membres de l'organisation
        members = self._get_members_by_type(organization_type, organization_id)
        
        if not members:
            return []
        
        member_list = list(members)
        random.shuffle(member_list)
        
        teams = []
        
        # Supprime les équipes existantes pour cette organisation
        organization = self.env['res.partner'].browse(organization_id)
        existing_teams = self._get_existing_teams(organization, organization_type)
        existing_teams.unlink()
        
        # Détermine le préfixe du nom d'équipe selon le type
        type_names = {
            'company': 'Équipe',
            'tribe': 'Équipe Tribu',
            'prayer_cell': 'Équipe Cellule',
            'group': 'Équipe Groupe',
            'academy': 'Équipe Structure'
        }
        team_prefix = type_names.get(organization_type, 'Équipe')
        
        for i in range(0, len(member_list), team_size):
            team_members = member_list[i:i + team_size]
            if team_members:
                team_name = f'{team_prefix} n° {len(teams) + 1}'
                team_lead = random.choice(team_members)
                
                # Prépare les valeurs pour créer l'équipe avec le bon type et la bonne organisation
                team_vals = {
                    'name': team_name,
                    'members_ids': [(6, 0, [member.id for member in team_members])],
                    'team_lead_id': team_lead.id,
                    'team_type': organization_type
                }
                
                # Définit l'organisation appropriée selon le type
                if organization_type == 'company':
                    team_vals['company_id'] = organization_id
                elif organization_type == 'tribe':
                    team_vals['tribe_id'] = organization_id
                elif organization_type == 'prayer_cell':
                    team_vals['prayer_cell_id'] = organization_id
                elif organization_type == 'group':
                    team_vals['group_id'] = organization_id
                elif organization_type == 'academy':
                    team_vals['academy_id'] = organization_id
                
                team = self.env['random.team'].sudo().create(team_vals)
                teams.append(team)
        
        return teams

    def _get_members_by_type(self, organization_type, organization_id):
        """Retourne les membres d'une organisation selon son type."""
        if organization_type == 'company':
            # Pour une compagnie, on récupère tous les contacts directs
            return self.env['res.partner'].search([
                ('is_company', '=', False),
                ('church_id', '=', organization_id)
            ])
        elif organization_type == 'tribe':
            # Pour une tribu, on récupère d'abord les membres directs de la tribu
            direct_members = self.env['res.partner'].search([
                ('is_company', '=', False),
                ('tribe_id', '=', organization_id)
            ])
            
            # Puis on récupère tous les membres des cellules de prière de cette tribu
            prayer_cells = self.env['res.partner'].search([
                ('is_company', '=', True),
                ('organization_type', '=', 'prayer_cell'),
                ('church_id', '=', organization_id)
            ])
            
            cell_members = self.env['res.partner']
            for cell in prayer_cells:
                members = self.env['res.partner'].search([
                    ('is_company', '=', False),
                    ('prayer_cell_id', '=', cell.id)
                ])
                cell_members |= members
            
            # On combine les membres directs et ceux des cellules (sans doublons)
            all_members = direct_members | cell_members
            return all_members
        elif organization_type == 'prayer_cell':
            return self.env['res.partner'].search([
                ('is_company', '=', False),
                ('prayer_cell_id', '=', organization_id)
            ])
        elif organization_type == 'group':
            return self.env['res.partner'].search([
                ('is_company', '=', False),
                ('group_id', '=', organization_id)
            ])
        elif organization_type == 'academy':
            return self.env['res.partner'].search([
                ('is_company', '=', False),
                ('academy_id', '=', organization_id)
            ])
        return self.env['res.partner']

    def _get_existing_teams(self, organization, organization_type):
        """Retourne les équipes existantes pour une organisation."""
        domain = []
        
        if organization_type == 'company':
            domain = [('team_type', '=', 'company'), ('company_id', '=', organization.id)]
        elif organization_type == 'tribe':
            domain = [('team_type', '=', 'tribe'), ('tribe_id', '=', organization.id)]
        elif organization_type == 'prayer_cell':
            domain = [('team_type', '=', 'prayer_cell'), ('prayer_cell_id', '=', organization.id)]
        elif organization_type == 'group':
            domain = [('team_type', '=', 'group'), ('group_id', '=', organization.id)]
        elif organization_type == 'academy':
            domain = [('team_type', '=', 'academy'), ('academy_id', '=', organization.id)]
        
        return self.env['random.team'].search(domain)

    def action_view_teams(self):
        """Action pour afficher les équipes de cette organisation."""
        if not self.is_company:
            return False
        
        org_type = self.organization_type if self.organization_type else 'company'
        teams = self._get_existing_teams(self, org_type)
        
        return {
            'name': f'Équipes de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'random.team',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', teams.ids)],
            'context': {'default_organization_id': self.id}
        }