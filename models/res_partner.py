from odoo import models, fields, api
from datetime import datetime, timedelta, date
import random
from odoo.exceptions import ValidationError  # <-- Cet import est crucial


class RandomTribe(models.Model):
    _name = "random.tribe"
    _description = "Tribu"

    name = fields.Char(string="Nom de la tribu", required=True)
    description = fields.Text(string="Description")


class RandomPrayerCell(models.Model):
    _name = "random.prayer.cell"
    _description = "Cellule de prière"

    name = fields.Char(string="Nom de la cellule de prière", required=True)
    description = fields.Text(string="Description")
    tribe_id = fields.Many2one(
        "random.tribe",
        string="Tribu associée",
        help="Tribu à laquelle cette cellule de prière est associée",
    )


# Extension du modèle res.partner pour la gestion des équipes et informations personnelles
class ResPartner(models.Model):
    _inherit = "res.partner"

    # Types d'organisation
    organization_type = fields.Selection(
        [
            ("company", "Église"),
            ("tribe", "Tribu"),
            ("prayer_cell", "Cellule de prière"),
            ("group", "Groupe"),
            ("region", "Région"),
            ("communication", "Communication"),
            ("artistic_group", "Groupe Artistique"),
            ("ngo", "ONG"),
            ("school", "École"),
            ("sports_group", "Groupe Sportif"),
            ("educational_group", "Groupe Éducatif"),
            ("other_group", "Autres Structures"),
        ],
        string="Type d'organisation",
    )

    # Relations spécialisées
    tribe_church_id = fields.Many2one(
        "res.partner",
        string="Église de la tribu",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    prayer_cell_tribe_id = fields.Many2one(
        "res.partner",
        string="Tribu de la cellule",
        domain="[('organization_type', '=', 'tribe')]",
    )
    prayer_cell_church_id = fields.Many2one(
        "res.partner",
        string="Église de la cellule",
        related="prayer_cell_tribe_id.tribe_church_id",
        store=True,
        readonly=True,
    )
    group_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )

    # Relations pour les nouveaux groupes
    communication_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe de communication",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    artistic_group_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe artistique",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    ngo_church_id = fields.Many2one(
        "res.partner",
        string="Église de l'ONG",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    school_church_id = fields.Many2one(
        "res.partner",
        string="Église de l'école",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    other_group_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe spécialisé",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    sports_group_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe sportif",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )
    educational_group_church_id = fields.Many2one(
        "res.partner",
        string="Église du groupe éducatif",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )

    prayer_cell_type_id = fields.Many2one(
        "random.prayer.cell",
        string="Type de cellule de prière",
        domain="[('id', '!=', False)]",
        help="Type de cellule de prière pour cette organisation",
    )
    tribe_type_id = fields.Many2one(
        "random.tribe",
        string="Type de tribu",
        domain="[('id', '!=', False)]",
        help="Type de tribu pour cette organisation",
    )

    # Affectations du fidèle
    church_id = fields.Many2one(
        "res.partner",
        string="Église",
        domain="[('organization_type', '=', 'company'), ('is_church', '=', True)]",
    )

    @api.depends_context("church_id")
    def _compute_tribe_domain(self):
        for rec in self:
            if rec.church_id:
                rec.tribe_domain = [
                    ("organization_type", "=", "tribe"),
                    ("tribe_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.tribe_domain = []

    tribe_domain = fields.Char(compute="_compute_tribe_domain")
    tribe_id = fields.Many2one(
        "res.partner",
        string="Tribu",
    )

    @api.depends_context("tribe_id")
    def _compute_prayer_cell_domain(self):
        for rec in self:
            if rec.tribe_id:
                rec.prayer_cell_domain = [
                    ("organization_type", "=", "prayer_cell"),
                    ("prayer_cell_tribe_id", "=", rec.tribe_id.id),
                ]
            else:
                rec.prayer_cell_domain = []

    prayer_cell_domain = fields.Char(compute="_compute_prayer_cell_domain")
    prayer_cell_id = fields.Many2one(
        "res.partner",
        string="Cellule de prière",
    )

    @api.depends_context("church_id")
    def _compute_group_domain(self):
        for rec in self:
            if rec.church_id:
                rec.group_domain = [
                    ("organization_type", "=", "group"),
                    ("group_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.group_domain = []

    group_domain = fields.Char(compute="_compute_group_domain")
    group_id = fields.Many2one(
        "res.partner",
        string="Groupe",
    )

    # ========== NOUVEAUX CHAMPS POUR LES GROUPES SPÉCIALISÉS ==========

    # Groupes de communication (Many2many car un membre peut appartenir à plusieurs groupes)
    @api.depends_context("church_id")
    def _compute_communication_domain(self):
        for rec in self:
            if rec.church_id:
                rec.communication_domain = [
                    ("organization_type", "=", "communication"),
                    ("communication_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.communication_domain = []

    communication_domain = fields.Char(compute="_compute_communication_domain")
    communication_ids = fields.Many2many(
        "res.partner",
        "partner_communication_rel",
        "partner_id",
        "communication_id",
        string="Groupes de communication",
        help="Groupes de communication auxquels ce membre appartient",
    )

    # Groupes de artistiques (Many2many)
    @api.depends_context("church_id")
    def _compute_artistic_domain(self):
        for rec in self:
            if rec.church_id:
                rec.artistic_domain = [
                    ("organization_type", "=", "artistic_group"),
                    ("artistic_group_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.artistic_domain = []

    artistic_domain = fields.Char(compute="_compute_artistic_domain")
    artistic_group_ids = fields.Many2many(
        "res.partner",
        "partner_artistic_group_rel",
        "partner_id",
        "artistic_group_id",
        string="Groupes artistiques",
        help="Groupes artistiques auxquels ce membre appartient",
    )

    # ONG (Many2many)
    @api.depends_context("church_id")
    def _compute_ngo_domain(self):
        for rec in self:
            if rec.church_id:
                rec.ngo_domain = [
                    ("organization_type", "=", "ngo"),
                    ("ngo_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.ngo_domain = []

    ngo_domain = fields.Char(compute="_compute_ngo_domain")
    ngo_ids = fields.Many2many(
        "res.partner",
        "partner_ngo_rel",
        "partner_id",
        "ngo_id",
        string="ONG",
        help="ONG auxquelles ce membre appartient",
    )

    # Écoles (Many2many)
    @api.depends_context("church_id")
    def _compute_school_domain(self):
        for rec in self:
            if rec.church_id:
                rec.school_domain = [
                    ("organization_type", "=", "school"),
                    ("school_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.school_domain = []

    school_domain = fields.Char(compute="_compute_school_domain")
    school_ids = fields.Many2many(
        "res.partner",
        "partner_school_rel",
        "partner_id",
        "school_id",
        string="Écoles",
        help="Écoles auxquelles ce membre appartient",
    )

    # Autres groupes (Many2many)
    @api.depends_context("church_id")
    def _compute_other_group_domain(self):
        for rec in self:
            if rec.church_id:
                rec.other_group_domain = [
                    ("organization_type", "=", "other_group"),
                    ("other_group_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.other_group_domain = []

    other_group_domain = fields.Char(compute="_compute_other_group_domain")
    other_group_ids = fields.Many2many(
        "res.partner",
        "partner_other_group_rel",
        "partner_id",
        "other_group_id",
        string="Groupes spécialisés",
        help="Groupes spécialisés auxquels ce membre appartient",
    )

    # Groupes sportifs (Many2many)
    @api.depends_context("church_id")
    def _compute_sports_group_domain(self):
        for rec in self:
            if rec.church_id:
                rec.sports_group_domain = [
                    ("organization_type", "=", "sports_group"),
                    ("sports_group_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.sports_group_domain = []

    sports_group_domain = fields.Char(compute="_compute_sports_group_domain")
    sports_group_ids = fields.Many2many(
        "res.partner",
        "partner_sports_group_rel",
        "partner_id",
        "sports_group_id",
        string="Groupes sportifs",
        help="Groupes sportifs auxquels ce membre appartient",
    )

    # Groupes éducatifs (Many2many)
    @api.depends_context("church_id")
    def _compute_educational_group_domain(self):
        for rec in self:
            if rec.church_id:
                rec.educational_group_domain = [
                    ("organization_type", "=", "educational_group"),
                    ("educational_group_church_id", "=", rec.church_id.id),
                ]
            else:
                rec.educational_group_domain = []

    educational_group_domain = fields.Char(compute="_compute_educational_group_domain")
    educational_group_ids = fields.Many2many(
        "res.partner",
        "partner_educational_group_rel",
        "partner_id",
        "educational_group_id",
        string="Groupes éducatifs",
        help="Groupes éducatifs auxquels ce membre appartient",
    )

    # Membres pour les nouveaux types d'organisations
    communication_members = fields.Many2many(
        "res.partner",
        "partner_communication_rel",
        "communication_id",
        "partner_id",
        string="Membres du groupe de communication",
    )
    artistic_group_members = fields.Many2many(
        "res.partner",
        "partner_artistic_group_rel",
        "artistic_group_id",
        "partner_id",
        string="Membres du groupe artistique",
    )
    ngo_members = fields.Many2many(
        "res.partner",
        "partner_ngo_rel",
        "ngo_id",
        "partner_id",
        string="Membres de l'ONG",
    )
    school_members = fields.Many2many(
        "res.partner",
        "partner_school_rel",
        "school_id",
        "partner_id",
        string="Membres de l'école",
    )
    other_group_members = fields.Many2many(
        "res.partner",
        "partner_other_group_rel",
        "other_group_id",
        "partner_id",
        string="Membres du groupe spécialisé",
    )
    sports_group_members = fields.Many2many(
        "res.partner",
        "partner_sports_group_rel",
        "sports_group_id",
        "partner_id",
        string="Membres du groupe sportif",
    )
    educational_group_members = fields.Many2many(
        "res.partner",
        "partner_educational_group_rel",
        "educational_group_id",
        "partner_id",
        string="Membres du groupe éducatif",
    )

    # Compteurs pour les nouveaux groupes
    communication_count = fields.Integer(
        string="Nombre de groupes de communication",
        compute="_compute_specialized_group_counts",
    )
    artistic_group_count = fields.Integer(
        string="Nombre de groupes artistiques",
        compute="_compute_specialized_group_counts",
    )
    ngo_count = fields.Integer(
        string="Nombre d'ONG", compute="_compute_specialized_group_counts"
    )
    school_count = fields.Integer(
        string="Nombre d'écoles", compute="_compute_specialized_group_counts"
    )
    other_group_count = fields.Integer(
        string="Nombre des groupes spécialisés",
        compute="_compute_specialized_group_counts",
    )
    sports_group_count = fields.Integer(
        string="Nombre de groupes sportifs", compute="_compute_specialized_group_counts"
    )
    educational_group_count = fields.Integer(
        string="Nombre de groupes éducatifs",
        compute="_compute_specialized_group_counts",
    )

    # Responsables pour les nouveaux groupes
    communication_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe de communication",
        domain="[('is_leader','=',True)]",
    )
    artistic_group_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe artistique",
        domain="[('is_leader','=',True)]",
    )
    ngo_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable de l'ONG",
        domain="[('is_leader','=',True)]",
    )
    school_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable de l'école",
        domain="[('is_leader','=',True)]",
    )
    other_group_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe spécialisé",
        domain="[('is_leader','=',True)]",
    )
    sports_group_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe sportif",
        domain="[('is_leader','=',True)]",
    )
    educational_group_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe éducatif",
        domain="[('is_leader','=',True)]",
    )

    # ========== FIN DES NOUVEAUX CHAMPS ==========

    region_id = fields.Many2one(
        "res.partner", string="Région", domain="[('organization_type', '=', 'region')]"
    )

    # Chef-lieu de région et pasteur régional
    @api.depends_context("region_id")
    def _compute_regional_capital_domain(self):
        for rec in self:
            if rec.region_id:
                # Filtre pour les partenaires de type "company" dans la même région
                rec.regional_capital_domain = [
                    ("organization_type", "=", "company"),
                    ("region_id", "=", rec.region_id.id),
                ]
            else:
                rec.regional_capital_domain = []

    regional_capital_domain = fields.Char(compute="_compute_regional_capital_domain")
    regional_capital_id = fields.Many2one(
        "res.partner",
        string="Chef-lieu de région",
    )

    regional_pastor_id = fields.Many2one(
        "res.partner",
        string="Pasteur régional",
        related="regional_capital_id.main_pastor_id",
        store=True,
        readonly=True,
    )
    # ========== NOUVELLES INFORMATIONS PERSONNELLES ==========

    # Sexe
    gender = fields.Selection(
        [
            ("male", "Homme"),
            ("female", "Femme"),
        ],
        string="Sexe",
    )

    # Date de naissance et âge
    birthdate = fields.Date(string="Date de naissance")
    age = fields.Integer(string="Âge", compute="_compute_age", store=True)

    # Situation matrimoniale
    marital_status = fields.Selection(
        [
            ("single", "Célibataire"),
            ("married", "Marié(e)"),
            ("divorced", "Divorcé(e)"),
            ("widowed", "Veuf/Veuve"),
            ("separated", "Séparé(e)"),
            ("cohabiting", "Concubinage"),
        ],
        string="Situation matrimoniale",
        default="single",
    )

    # Conjoint
    spouse_id = fields.Many2one(
        "res.partner",
        string="Conjoint(e)",
        domain="[('is_company', '=', False), ('id', '!=', id)]",
    )

    # Enfants

    father_id = fields.Many2one(
        "res.partner",
        string="Père",
        domain=[("gender", "=", "male"), ("is_company", "=", False)],
    )
    mother_id = fields.Many2one(
        "res.partner",
        string="Mère",
        domain=[("gender", "=", "female"), ("is_company", "=", False)],
    )
    children_from_father_ids = fields.One2many(
        "res.partner",
        inverse_name="father_id",
        string="Enfants (père)",
        domain="[('father_id', '=', id)]",
    )
    children_from_mother_ids = fields.One2many(
        "res.partner",
        inverse_name="mother_id",
        string="Enfants (mère)",
        domain="[('mother_id', '=', id)]",
    )

    @api.constrains("father_id", "mother_id")
    def _check_parents_different(self):
        for record in self:
            if (
                record.father_id
                and record.mother_id
                and record.father_id == record.mother_id
            ):
                raise ValidationError(
                    "Le père et la mère doivent être deux personnes différentes."
                )

    # Compteur d'enfants
    mother_children_count = fields.Integer(
        string="Nombre d'enfants de la mère", compute="_compute_mother_children_count"
    )
    father_children_count = fields.Integer(
        string="Nombre d'enfants du père", compute="_compute_father_children_count"
    )

    # Date de salut et statut nouveau
    arrival_date = fields.Date(
        string="Date de salut", default=fields.Date.context_today
    )
    is_new_member = fields.Boolean(
        string="Nouveau membre", compute="_compute_is_new_member", store=False
    )

    # ========== FIN NOUVELLES INFORMATIONS ==========

    # Membres par type d'organisation
    prayer_cell_members = fields.One2many(
        "res.partner", "prayer_cell_id", string="Membres de la cellule"
    )
    group_members = fields.One2many(
        "res.partner", "group_id", string="Membres du groupe"
    )
    tribe_members = fields.One2many(
        "res.partner", "tribe_id", string="Membres de la tribu"
    )
    company_contacts = fields.One2many(
        "res.partner", "church_id", string="Membres de l'église"
    )

    # Champs calculés pour afficher les équipes de chaque type
    company_team_ids = fields.Many2many(
        "random.team", compute="_compute_team_memberships", string="Équipes Compagnie"
    )
    tribe_team_ids = fields.Many2many(
        "random.team", compute="_compute_team_memberships", string="Équipes Tribu"
    )
    prayer_cell_team_ids = fields.Many2many(
        "random.team", compute="_compute_team_memberships", string="Équipes Cellule"
    )
    group_team_ids = fields.Many2many(
        "random.team", compute="_compute_team_memberships", string="Équipes Groupe"
    )

    # Compteurs pour les boutons intelligents (organisations)
    team_count = fields.Integer(
        string="Nombre d'équipes", compute="_compute_organization_counts"
    )
    tribe_count = fields.Integer(
        string="Nombre de tribus", compute="_compute_organization_counts"
    )
    prayer_cell_count = fields.Integer(
        string="Nombre de cellules", compute="_compute_organization_counts"
    )
    group_count = fields.Integer(
        string="Nombre de groupes", compute="_compute_organization_counts"
    )

    # Compteurs pour les boutons intelligents (contacts individuels)
    total_teams_count = fields.Integer(
        string="Total équipes", compute="_compute_team_counts"
    )
    company_teams_count = fields.Integer(
        string="Équipes Compagnie", compute="_compute_team_counts"
    )
    tribe_teams_count = fields.Integer(
        string="Équipes Tribu", compute="_compute_team_counts"
    )
    prayer_cell_teams_count = fields.Integer(
        string="Équipes Cellule", compute="_compute_team_counts"
    )
    group_teams_count = fields.Integer(
        string="Équipes Groupe", compute="_compute_team_counts"
    )

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
    is_birthday = fields.Boolean(
        string="Anniversaire aujourd'hui", compute="_compute_is_birthday", store=False
    )

    # Champ pour suivre si l'alerte a déjà été envoyée aujourd'hui
    birthday_alert_sent = fields.Boolean(
        string="Alerte anniversaire envoyée", default=False
    )

    # Critères de sexe pour les groupes
    required_gender = fields.Selection(
        [
            ("male", "Hommes seulement"),
            ("female", "Femmes seulement"),
            ("mixed", "Mixte (hommes et femmes)"),
        ],
        string="Sexe requis",
        default="mixed",
        invisible=lambda self: not self._is_age_group(),
        help="Définit si le groupe est réservé aux hommes, aux femmes ou mixte",
    )

    # Critère de situation matrimoniale pour les groupes
    marital_requirement = fields.Selection(
        [
            ("any", "Toutes situations"),
            ("married_only", "Mariés seulement"),
            ("single_only", "Célibataires seulement"),
        ],
        string="Situation matrimoniale requise",
        default="any",
        invisible=lambda self: not self._is_age_group(),
        help="Définit si le groupe accepte seulement les personnes mariées, seulement les célibataires ou toutes situations",
    )

    # Pour les églises
    is_church = fields.Boolean(string="Est une église")
    is_in_a_church = fields.Boolean(
        string="Est dans une église",
        related="church_id.is_church",
        readonly=True,
        store=True,
    )
    main_pastor_id = fields.Many2one(
        "res.partner",
        string="Pasteur principal",
        domain="[('is_pastor','=',True), ('church_id','=',id)]",
    )
    # Pour les pasteurs adjoints
    assistant_pastor_ids = fields.Many2many(
        "res.partner",
        "church_assistant_pastor_rel",  # Nom explicite de la table de relation
        "church_id",
        "pastor_id",
        string="Pasteurs adjoints",
        domain="[('is_pastor','=',True), ('church_id','=',id)]",
    )
    parent_church_id = fields.Many2one(
        "res.partner", string="Église mère", domain="[('is_church','=',True)]"
    )

    # Pour les membres
    is_pastor = fields.Boolean(string="Pasteur")
    is_elder = fields.Boolean(string="Ancien")
    is_deacon = fields.Boolean(string="Diacre")
    is_missionary = fields.Boolean(string="Missionnaire")
    is_leader = fields.Boolean(string="Responsable")
    is_pastor_wife = fields.Boolean(string="Femme de pasteur")
    church_id = fields.Many2one(
        "res.partner", string="Église", domain="[('is_church','=',True)]"
    )

    # Responsables des organisations
    group_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable du groupe",
        domain="[('is_leader','=',True), ('group_id','=',id)]",
    )
    # Pour les responsables adjoints de groupe
    group_assistant_leader_ids = fields.Many2many(
        "res.partner",
        "group_assistant_leader_rel",
        "group_id",
        "leader_id",
        string="Responsables adjoints du groupe",
        domain="[('is_leader','=',True), ('group_id','=',id)]",
    )

    prayer_cell_leader_id = fields.Many2one(
        "res.partner",
        string="Responsable de la cellule",
        domain="[('is_leader','=',True), ('prayer_cell_id','=',id)]",
    )
    # Pour les responsables adjoints de cellule
    prayer_cell_assistant_leader_ids = fields.Many2many(
        "res.partner",
        "cell_assistant_leader_rel",
        "cell_id",
        "leader_id",
        string="Responsables adjoints de la cellule",
        domain="[('is_leader','=',True), ('prayer_cell_id','=',id)]",
    )
    prayer_cell_follower_id = fields.Many2one(
        "res.partner",
        string="Responsable de suivi de la cellule",
        domain="[('is_elder','=',True)]",
    )

    # Champ calculé pour compter les églises filles
    child_church_count = fields.Integer(
        string="Nombre d'églises filles", compute="_compute_child_church_count"
    )
    regional_church_count = fields.Integer(
        string="Nombre d'églises régionales", compute="_compute_regional_church_count"
    )

    # Champ pour stocker le code unique
    unique_code = fields.Char(
        string="Code unique",
        readonly=True,
        copy=False,
        index=True,
        help="Code unique généré automatiquement pour identifier ce partenaire",
    )

    # Ajouter dans la classe ResPartner(models.Model)
    # Pour les écoles
    school_monitor_ids = fields.Many2many(
        'res.partner',
        'school_monitor_rel',
        'school_id',
        'monitor_id',
        string='Moniteurs/Professeurs',
        domain="[('id', '!=', id), '|', ('is_teacher', '=', True), ('is_monitor', '=', True)]",
        help="Moniteurs ou professeurs de cette école"
    )

    is_monitor = fields.Boolean(string="Est moniteur")
    is_teacher = fields.Boolean(string="Est professeur")

    # Compteur de moniteurs/professeurs
    monitor_count = fields.Integer(
        string="Nombre de moniteurs/professeurs",
        compute="_compute_monitor_count",
        store=True
    )

    @api.depends('school_monitor_ids')
    def _compute_monitor_count(self):
        for record in self:
            record.monitor_count = len(record.school_monitor_ids)

    # Méthode pour ouvrir la vue des moniteurs/professeurs
    def action_view_school_monitors(self):
        self.ensure_one()
        return {
            'name': f"Moniteurs/Professeurs de {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.school_monitor_ids.ids)],
            'context': {
                'default_is_monitor': True,
                'search_default_is_monitor': True,
                'search_default_is_teacher': True
            }
        }

    @api.model
    def create(self, vals):
        """Générer un code unique lors de la création"""
        if not vals.get("unique_code"):
            vals["unique_code"] = self._generate_unique_code(vals)
        return super(ResPartner, self).create(vals)

    def _generate_unique_code(self, vals=None):
        """
        Génère un code unique basé sur le type d'organisation et d'autres critères
        Format : [PREFIXE][ANNEE][NUMERO_SEQUENCE]
        """
        if vals is None:
            vals = {}

        # Déterminer le préfixe selon le type d'organisation ou si c'est une personne
        prefixes = {
            "company": "EGL",  # Église
            "tribe": "TRB",  # Tribu
            "prayer_cell": "CEL",  # Cellule de prière
            "group": "GRP",  # Groupe
            "region": "REG",  # Région
            "communication": "COM",  # Communication
            "artistic_group": "ART",  # Groupe Artistique
            "ngo": "ONG",  # ONG
            "school": "ECO",  # École
            "sports_group": "SPO",  # Groupe Sportif
            "educational_group": "EDU",  # Groupe Éducatif
            "other_group": "AUT",  # Autres Structures
        }

        organization_type = vals.get("organization_type") or self.organization_type
        is_company = vals.get(
            "is_company", self.is_company if hasattr(self, "is_company") else False
        )

        if organization_type and organization_type in prefixes:
            prefix = prefixes[organization_type]
        elif is_company:
            prefix = "ENT"  # Entreprise générique
        else:
            prefix = "PER"  # Personne physique

        # Année courante
        current_year = fields.Date.today().year
        year_suffix = str(current_year)[2:]  # Les 2 derniers chiffres de l'année

        # Générer un numéro de séquence unique
        sequence_number = self._get_next_sequence_number(prefix, year_suffix)

        # Format final : PREFIXE + ANNEE + NUMERO (ex: EGL24001, PER24001, etc.)
        unique_code = f"{prefix}{year_suffix}{sequence_number:04d}"

        return unique_code

    def _get_next_sequence_number(self, prefix, year_suffix):
        """
        Génère le prochain numéro de séquence pour un préfixe et année donnés
        """
        # Rechercher le dernier code avec ce préfixe et cette année
        pattern = f"{prefix}{year_suffix}%"

        last_partner = self.env["res.partner"].search(
            [("unique_code", "like", pattern)], order="unique_code desc", limit=1
        )

        if last_partner and last_partner.unique_code:
            # Extraire le numéro de séquence du dernier code
            try:
                last_number = int(
                    last_partner.unique_code[-4:]
                )  # Les 4 derniers chiffres
                return last_number + 1
            except (ValueError, IndexError):
                return 1
        else:
            return 1

    @api.model
    def generate_codes_for_existing_partners(self):
        """
        Méthode utilitaire pour générer des codes pour les partenaires existants
        qui n'en ont pas encore
        """
        partners_without_code = self.search([("unique_code", "=", False)])

        for partner in partners_without_code:
            partner.unique_code = partner._generate_unique_code()

        return len(partners_without_code)

    @api.constrains("unique_code")
    def _check_unique_code(self):
        """Vérifier que le code unique est vraiment unique"""
        for record in self:
            if record.unique_code:
                duplicate = self.search(
                    [("unique_code", "=", record.unique_code), ("id", "!=", record.id)],
                    limit=1,
                )
                if duplicate:
                    raise ValidationError(
                        f"Le code unique '{record.unique_code}' existe déjà pour un autre partenaire."
                    )

    def regenerate_unique_code(self):
        """
        Méthode pour régénérer le code unique (utile en cas de problème)
        """
        for record in self:
            record.unique_code = record._generate_unique_code()

    def name_get(self):
        """
        Surcharger name_get pour inclure le code unique dans l'affichage
        """
        result = []
        for record in self:
            name = record.name or ""
            if record.unique_code:
                name = f"[{record.unique_code}] {name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """
        Permettre la recherche par code unique
        """
        if args is None:
            args = []

        # Si le terme de recherche ressemble à un code (commence par des lettres majuscules)
        if name and len(name) >= 3 and name[:3].isupper():
            # Rechercher d'abord par code unique
            partners = self.search(
                [("unique_code", operator, name)] + args, limit=limit
            )
            if partners:
                return partners.name_get()

        # Sinon, utiliser la recherche normale
        return super(ResPartner, self).name_search(name, args, operator, limit)

    # Méthodes utilitaires pour obtenir des statistiques sur les codes
    @api.model
    def get_code_statistics(self):
        """
        Retourne des statistiques sur les codes générés
        """
        current_year = fields.Date.today().year
        year_suffix = str(current_year)[2:]

        prefixes = [
            "EGL",
            "TRB",
            "CEL",
            "GRP",
            "REG",
            "COM",
            "ART",
            "ONG",
            "ECO",
            "SPO",
            "EDU",
            "AUT",
            "ENT",
            "PER",
        ]
        stats = {}

        for prefix in prefixes:
            count = self.search_count(
                [("unique_code", "like", f"{prefix}{year_suffix}%")]
            )
            if count > 0:
                stats[prefix] = count

        return stats

    # ========== NOUVELLES MÉTHODES DE CALCUL POUR LES GROUPES SPÉCIALISÉS ==========

    @api.depends()
    def _compute_specialized_group_counts(self):
        """Calcule le nombre de groupes spécialisés pour les églises."""
        for partner in self:
            if partner.is_company and partner.is_church:
                partner.communication_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "communication"),
                        ("communication_church_id", "=", partner.id),
                    ]
                )
                partner.artistic_group_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "artistic_group"),
                        ("artistic_group_church_id", "=", partner.id),
                    ]
                )
                partner.ngo_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "ngo"),
                        ("ngo_church_id", "=", partner.id),
                    ]
                )
                partner.school_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "school"),
                        ("school_church_id", "=", partner.id),
                    ]
                )
                partner.other_group_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "other_group"),
                        ("other_group_church_id", "=", partner.id),
                    ]
                )
                partner.sports_group_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "sports_group"),
                        ("sports_group_church_id", "=", partner.id),
                    ]
                )
                partner.educational_group_count = self.env["res.partner"].search_count(
                    [
                        ("is_company", "=", True),
                        ("organization_type", "=", "educational_group"),
                        ("educational_group_church_id", "=", partner.id),
                    ]
                )
            else:
                partner.communication_count = 0
                partner.artistic_group_count = 0
                partner.ngo_count = 0
                partner.school_count = 0
                partner.other_group_count = 0
                partner.sports_group_count = 0
                partner.educational_group_count = 0

    # ========== ACTIONS POUR LES NOUVEAUX GROUPES SPÉCIALISÉS ==========

    def action_view_communications(self):
        """Action pour afficher les groupes de communication de cette église."""
        if not self.is_company or not self.is_church:
            return False

        communications = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "communication"),
                ("communication_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes de communication de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", communications.ids)],
            "context": {
                "default_organization_type": "communication",
                "default_communication_church_id": self.id,
            },
        }

    def action_view_artistic_groups(self):
        """Action pour afficher les groupes de danse de cette église."""
        if not self.is_company or not self.is_church:
            return False

        artistic_groups = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "artistic_group"),
                ("artistic_group_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes artistiques de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", artistic_groups.ids)],
            "context": {
                "default_organization_type": "artistic_group",
                "default_artistic_group_church_id": self.id,
            },
        }

    def action_view_ngos(self):
        """Action pour afficher les ONG de cette église."""
        if not self.is_company or not self.is_church:
            return False

        ngos = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "ngo"),
                ("ngo_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"ONG de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", ngos.ids)],
            "context": {
                "default_organization_type": "ngo",
                "default_ngo_church_id": self.id,
            },
        }

    def action_view_schools(self):
        """Action pour afficher les écoles de cette église."""
        if not self.is_company or not self.is_church:
            return False

        schools = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "school"),
                ("school_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Écoles de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", schools.ids)],
            "context": {
                "default_organization_type": "school",
                "default_school_church_id": self.id,
            },
        }

    def action_view_other_groups(self):
        """Action pour afficher les groupes spécialisés de cette église."""
        if not self.is_company or not self.is_church:
            return False

        other_groups = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "other_group"),
                ("other_group_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes spécialisés de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", other_groups.ids)],
            "context": {
                "default_organization_type": "other_group",
                "default_other_group_church_id": self.id,
            },
        }

    def action_view_sports_groups(self):
        """Action pour afficher les groupes sportifs de cette église."""
        if not self.is_company or not self.is_church:
            return False

        sports_groups = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "sports_group"),
                ("sports_group_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes sportifs de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", sports_groups.ids)],
            "context": {
                "default_organization_type": "sports_group",
                "default_sports_group_church_id": self.id,
            },
        }

    def action_view_educational_groups(self):
        """Action pour afficher les groupes éducatifs de cette église."""
        if not self.is_company or not self.is_church:
            return False

        educational_groups = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "educational_group"),
                ("educational_group_church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes éducatifs de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", educational_groups.ids)],
            "context": {
                "default_organization_type": "educational_group",
                "default_educational_group_church_id": self.id,
            },
        }

    # ========== MÉTHODES EXISTANTES (MAINTENUES POUR COMPATIBILITÉ) ==========

    def _compute_regional_church_count(self):
        """Calcule le nombre d'églises régionales associées à cette région."""
        for partner in self:
            if partner.organization_type == "region":
                partner.regional_church_count = self.search_count(
                    [("region_id", "=", partner.id), ("is_church", "=", True)]
                )
            else:
                partner.regional_church_count = 0

    def action_view_regional_churches(self):
        """Action pour voir les églises régionales associées à cette région."""
        self.ensure_one()
        if self.organization_type != "region":
            return False
        return {
            "name": f"Églises régionales de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("region_id", "=", self.id), ("is_church", "=", True)],
            "context": {"default_region_id": self.id, "default_is_church": True},
        }

    def action_validate_inscription(self):
        self.ensure_one()
        self.write({"active": True})
        return True

    def action_archive(self):
        self.ensure_one()
        self.write({"active": False})
        return True

    def _compute_child_church_count(self):
        for partner in self:
            partner.child_church_count = self.search_count(
                [("parent_church_id", "=", partner.id), ("is_church", "=", True)]
            )

    def action_view_child_churches(self):
        self.ensure_one()
        return {
            "name": f"Églises filles de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("parent_church_id", "=", self.id), ("is_church", "=", True)],
            "context": {"default_parent_church_id": self.id, "default_is_church": True},
        }

    @api.constrains("is_pastor_wife", "spouse_id")
    def _check_pastor_wife(self):
        for partner in self:
            if partner.is_pastor_wife and (
                not partner.spouse_id or not partner.spouse_id.is_pastor
            ):
                raise ValidationError(
                    "Une femme de pasteur doit avoir un conjoint qui est pasteur"
                )

    @api.onchange("spouse_id")
    def _onchange_spouse_id(self):
        if self.gender == "female" and self.spouse_id and self.spouse_id.is_pastor:
            self.is_pastor_wife = True
        elif self.gender == "female" and not (
            self.spouse_id and self.spouse_id.is_pastor
        ):
            self.is_pastor_wife = False

    @api.depends("birthdate")
    def _compute_is_birthday(self):
        """Détermine si c'est l'anniversaire du contact aujourd'hui."""
        today = date.today()
        for partner in self:
            if partner.birthdate:
                birthdate = fields.Date.from_string(partner.birthdate)
                partner.is_birthday = (
                    birthdate.month == today.month and birthdate.day == today.day
                )
            else:
                partner.is_birthday = False

    @api.model
    def _cron_check_birthdays(self):
        """Méthode appelée par le cron pour vérifier les anniversaires."""
        today = date.today()
        birthday_contacts = self.search(
            [
                ("birthdate", "!=", False),
                ("is_company", "=", False),
                ("birthday_alert_sent", "=", False),
                ("active", "=", True),
            ]
        ).filtered(
            lambda p: fields.Date.from_string(p.birthdate).month == today.month
            and fields.Date.from_string(p.birthdate).day == today.day
        )

        if birthday_contacts:
            self._send_birthday_alerts(birthday_contacts)
            birthday_contacts.write({"birthday_alert_sent": True})

        yesterday = today - timedelta(days=1)
        self.search(
            [
                ("birthday_alert_sent", "=", True),
                ("birthdate", "!=", False),
                ("active", "=", True),
            ]
        ).filtered(
            lambda p: fields.Date.from_string(p.birthdate).month != today.month
            or fields.Date.from_string(p.birthdate).day != today.day
        ).write(
            {"birthday_alert_sent": False}
        )

    def _send_birthday_alerts(self, contacts):
        """Envoie les notifications d'anniversaire."""
        for contact in contacts:
            self.env["mail.activity"].create(
                {
                    "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                    "summary": f"Anniversaire de {contact.name}",
                    "note": f"Aujourd'hui c'est l'anniversaire de {contact.name} ({contact.age} ans). Pensez à lui souhaiter un bon anniversaire!",
                    "user_id": self.env.user.id,
                    "res_id": contact.id,
                    "res_model_id": self.env["ir.model"]._get("res.partner").id,
                    "date_deadline": fields.Date.today(),
                }
            )

            partner_ids = self.env["res.users"].search([]).mapped("partner_id").ids
            if partner_ids:
                self.env["mail.message"].create(
                    {
                        "message_type": "notification",
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        "body": f"🎉 Aujourd'hui c'est l'anniversaire de <b>{contact.name}</b> ({contact.age} ans). Pensez à lui souhaiter un bon anniversaire!",
                        "subject": f"Anniversaire de {contact.name}",
                        "partner_ids": [(6, 0, partner_ids)],
                        "model": "res.partner",
                        "res_id": contact.id,
                    }
                )

    def _is_age_group(self):
        """Détermine si ce partenaire est un groupe avec tranche d'âge"""
        return self.is_company and self.organization_type == "group"

    @api.depends("birthdate")
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

    @api.depends("children_from_mother_ids")
    def _compute_mother_children_count(self):
        """Calcule le nombre d'enfants."""
        for partner in self:
            partner.mother_children_count = len(partner.children_from_mother_ids)

    @api.depends("children_from_father_ids")
    def _compute_father_children_count(self):
        """Calcule le nombre d'enfants."""
        for partner in self:
            partner.father_children_count = len(partner.children_from_father_ids)

    @api.depends("arrival_date")
    def _compute_is_new_member(self):
        """Détermine si le membre est nouveau selon la durée configurée"""
        duration = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("random_team_generator.new_member_duration", 30)
        )
        for partner in self:
            if partner.arrival_date and not partner.is_company:
                today = fields.Date.context_today(self)
                limit_date = today - timedelta(days=duration)
                partner.is_new_member = partner.arrival_date > limit_date
            else:
                partner.is_new_member = False

    @api.onchange("birthdate")
    def _onchange_birthdate(self):
        """Met à jour l'âge et le groupe lorsque la date de naissance change."""
        if self.birthdate:
            self._compute_age()
            self._assign_age_group()

    def _assign_age_group(self):
        """Assigne automatiquement le groupe en fonction de l'âge, du sexe et de la situation matrimoniale."""
        if not self.is_company and self.age > 0:
            domain = [
                ("is_company", "=", True),
                ("organization_type", "=", "group"),
                ("min_age", "<=", self.age),
                ("max_age", ">=", self.age),
            ]

            if self.gender:
                domain += [
                    "|",
                    ("required_gender", "=", "mixed"),
                    ("required_gender", "=", self.gender),
                ]

            if self.marital_status:
                domain += [
                    "|",
                    ("marital_requirement", "=", "any"),
                    "|",
                    "&",
                    ("marital_requirement", "=", "married_only"),
                    ("marital_status", "=", "married"),
                    "&",
                    ("marital_requirement", "=", "single_only"),
                    (
                        "marital_status",
                        "in",
                        ["single", "divorced", "widowed", "separated", "cohabiting"],
                    ),
                ]

            age_group = self.env["res.partner"].search(domain, limit=1)
            if age_group:
                self.group_id = age_group.id

    @api.constrains("required_gender", "marital_requirement")
    def _check_group_requirements(self):
        """Vérifie que les critères du groupe sont cohérents."""
        for group in self.filtered(lambda r: r._is_age_group()):
            if group.required_gender not in ["male", "female", "mixed"]:
                raise ValidationError(
                    "Le sexe requis doit être 'Hommes seulement', 'Femmes seulement' ou 'Mixte'"
                )
            if group.marital_requirement not in ["any", "married_only", "single_only"]:
                raise ValidationError(
                    "La situation matrimoniale requise doit être 'Toutes situations', 'Mariés seulement' ou 'Célibataires seulement'"
                )

    @api.constrains("min_age", "max_age")
    def _check_age_range(self):
        """Vérifie que la tranche d'âge est valide"""
        for group in self.filtered(lambda r: r._is_age_group()):
            if group.min_age < 0:
                raise ValidationError("L'âge minimum ne peut pas être négatif")
            if group.max_age < 0:
                raise ValidationError("L'âge maximum ne peut pas être négatif")
            if group.min_age > group.max_age:
                raise ValidationError(
                    "L'âge minimum ne peut pas être supérieur à l'âge maximum"
                )
            if group.max_age > 120:
                raise ValidationError("L'âge maximum ne peut pas dépasser 120 ans")

    @api.constrains("spouse_id")
    def _check_spouse_reciprocity(self):
        """Vérifie que la relation de mariage est réciproque."""
        for partner in self:
            if partner.spouse_id and partner.spouse_id.spouse_id != partner:
                partner.spouse_id.spouse_id = partner
                if partner.spouse_id.marital_status != "married":
                    partner.spouse_id.marital_status = "married"

    @api.constrains("marital_status", "spouse_id")
    def _check_marital_consistency(self):
        """Vérifie la cohérence entre le statut marital et le conjoint."""
        for partner in self:
            if partner.marital_status == "married" and not partner.spouse_id:
                pass
            elif partner.marital_status != "married" and partner.spouse_id:
                partner.marital_status = "married"

    @api.onchange("marital_status")
    def _onchange_marital_status(self):
        """Nettoie le champ conjoint si le statut n'est plus marié."""
        if self.marital_status != "married":
            self.spouse_id = False

    def action_view_children(self):
        if self.is_company:
            return False
        domain = ["|", ("father_id", "=", self.id), ("mother_id", "=", self.id)]
        return {
            "name": f"Enfants de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {
                "default_father_id": self.id if self.gender == "male" else False,
                "default_mother_id": self.id if self.gender == "female" else False,
                "default_is_company": False,
            },
        }

    def action_view_group_members_by_age(self):
        """Action pour afficher les membres du groupe filtrés par tranche d'âge, sexe et situation matrimoniale."""
        if not self.is_company or self.organization_type != "group":
            return False

        domain = [
            ("is_company", "=", False),
            ("group_id", "=", self.id),
            ("age", ">=", self.min_age),
            ("age", "<=", self.max_age),
        ]

        if self.required_gender != "mixed":
            domain.append(("gender", "=", self.required_gender))

        if self.marital_requirement == "married_only":
            domain.append(("marital_status", "=", "married"))
        elif self.marital_requirement == "single_only":
            domain.append(
                (
                    "marital_status",
                    "in",
                    ["single", "divorced", "widowed", "separated", "cohabiting"],
                )
            )

        return {
            "name": f"Membres du groupe {self.name} (Âge: {self.min_age}-{self.max_age})",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {"default_group_id": self.id},
        }

    @api.depends()
    def _compute_organization_counts(self):
        """Calcule le nombre d'organisations enfants et d'équipes pour les organisations."""
        for partner in self:
            if partner.is_company:
                org_type = (
                    partner.organization_type
                    if partner.organization_type
                    else "company"
                )

                teams = self._get_existing_teams(partner, org_type)
                partner.team_count = len(teams)

                if org_type == "company":
                    partner.tribe_count = self.env["res.partner"].search_count(
                        [
                            ("is_company", "=", True),
                            ("organization_type", "=", "tribe"),
                            ("church_id", "=", partner.id),
                        ]
                    )
                    partner.group_count = self.env["res.partner"].search_count(
                        [
                            ("is_company", "=", True),
                            ("organization_type", "=", "group"),
                            ("church_id", "=", partner.id),
                        ]
                    )
                    partner.prayer_cell_count = 0
                elif org_type == "tribe":
                    partner.prayer_cell_count = self.env["res.partner"].search_count(
                        [
                            ("is_company", "=", True),
                            ("organization_type", "=", "prayer_cell"),
                            ("church_id", "=", partner.id),
                        ]
                    )
                    partner.tribe_count = 0
                    partner.group_count = 0
                else:
                    partner.tribe_count = 0
                    partner.prayer_cell_count = 0
                    partner.group_count = 0
            else:
                partner.team_count = 0
                partner.tribe_count = 0
                partner.prayer_cell_count = 0
                partner.group_count = 0

    @api.depends()
    def _compute_team_memberships(self):
        """Calcule les équipes dont fait partie ce contact."""
        for partner in self:
            if partner.is_company:
                partner.company_team_ids = False
                partner.tribe_team_ids = False
                partner.prayer_cell_team_ids = False
                partner.group_team_ids = False
            else:
                all_teams = self.env["random.team"].search(
                    [("members_ids", "in", partner.id)]
                )

                partner.company_team_ids = all_teams.filtered(
                    lambda t: t.team_type == "company"
                )
                partner.tribe_team_ids = all_teams.filtered(
                    lambda t: t.team_type == "tribe"
                )
                partner.prayer_cell_team_ids = all_teams.filtered(
                    lambda t: t.team_type == "prayer_cell"
                )
                partner.group_team_ids = all_teams.filtered(
                    lambda t: t.team_type == "group"
                )

    @api.depends()
    def _compute_team_counts(self):
        """Calcule le nombre d'équipes par type."""
        for partner in self:
            if partner.is_company:
                partner.company_teams_count = 0
                partner.tribe_teams_count = 0
                partner.prayer_cell_teams_count = 0
                partner.group_teams_count = 0
                partner.total_teams_count = 0
            else:
                partner.company_teams_count = len(partner.company_team_ids)
                partner.tribe_teams_count = len(partner.tribe_team_ids)
                partner.prayer_cell_teams_count = len(partner.prayer_cell_team_ids)
                partner.group_teams_count = len(partner.group_team_ids)
                partner.total_teams_count = (
                    partner.company_teams_count
                    + partner.tribe_teams_count
                    + partner.prayer_cell_teams_count
                    + partner.group_teams_count
                )

    def action_view_tribes(self):
        """Action pour afficher les tribus de cette compagnie."""
        if not self.is_company or (
            self.organization_type and self.organization_type != "company"
        ):
            return False

        tribes = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "tribe"),
                ("church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Tribus de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", tribes.ids)],
        }

    def action_view_prayer_cells(self):
        """Action pour afficher les cellules de prière."""
        if not self.is_company:
            return False

        if (
            not self.organization_type or self.organization_type == "company"
        ) or self.organization_type == "tribe":
            prayer_cells = self.env["res.partner"].search(
                [
                    ("is_company", "=", True),
                    ("organization_type", "=", "prayer_cell"),
                    ("church_id", "=", self.id),
                ]
            )

            return {
                "name": f"Cellules de prière de {self.name}",
                "type": "ir.actions.act_window",
                "res_model": "res.partner",
                "view_mode": "tree,form",
                "domain": [("id", "in", prayer_cells.ids)],
            }
        return False

    def action_view_groups(self):
        """Action pour afficher les groupes de cette compagnie."""
        if not self.is_company or (
            self.organization_type and self.organization_type != "company"
        ):
            return False

        groups = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("organization_type", "=", "group"),
                ("church_id", "=", self.id),
            ]
        )

        return {
            "name": f"Groupes de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", groups.ids)],
        }

    def action_view_my_teams(self):
        """Action pour afficher toutes les équipes de ce contact."""
        if self.is_company:
            return False

        all_teams = self.env["random.team"].search([("members_ids", "in", self.id)])

        return {
            "name": f"Équipes de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "random.team",
            "view_mode": "tree,form",
            "domain": [("id", "in", all_teams.ids)],
        }

    def action_view_teams_by_type(self, team_type):
        """Action pour afficher les équipes d'un type spécifique."""
        if self.is_company:
            return False

        teams = self.env["random.team"].search(
            [("members_ids", "in", self.id), ("team_type", "=", team_type)]
        )

        type_names = {
            "company": "Compagnie",
            "tribe": "Tribu",
            "prayer_cell": "Cellule de prière",
            "group": "Groupe",
        }

        return {
            "name": f"Équipes {type_names.get(team_type, '')} de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "random.team",
            "view_mode": "tree,form",
            "domain": [("id", "in", teams.ids)],
        }

    def debug_members(self):
        """Méthode de debug pour vérifier les membres d'une organisation."""
        if not self.is_company:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Debug",
                    "message": "Cette méthode fonctionne uniquement sur les organisations (is_company=True)",
                    "type": "warning",
                },
            }

        org_type = self.organization_type if self.organization_type else "company"
        members = self._get_members_by_type(org_type, self.id)

        debug_info = []
        debug_info.append(f"Organisation: {self.name}")
        debug_info.append(f"Type: {org_type}")
        debug_info.append(f"ID: {self.id}")
        debug_info.append(f"Nombre de membres trouvés: {len(members)}")

        if org_type == "tribe":
            direct_members = self.env["res.partner"].search(
                [("is_company", "=", False), ("tribe_id", "=", self.id)]
            )
            prayer_cells = self.env["res.partner"].search(
                [
                    ("is_company", "=", True),
                    ("organization_type", "=", "prayer_cell"),
                    ("church_id", "=", self.id),
                ]
            )
            debug_info.append(f"Membres directs de la tribu: {len(direct_members)}")
            debug_info.append(f"Cellules de prière: {len(prayer_cells)}")

            for cell in prayer_cells:
                cell_members = self.env["res.partner"].search(
                    [("is_company", "=", False), ("prayer_cell_id", "=", cell.id)]
                )
                debug_info.append(f"  - {cell.name}: {len(cell_members)} membres")

        if members:
            debug_info.append("Membres:")
            for member in members:
                debug_info.append(f"  - {member.name}")

        message = "\n".join(debug_info)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Debug - Membres de l'organisation",
                "message": message,
                "type": "info",
                "sticky": True,
            },
        }

    def generate_random_teams(self):
        """Génère des équipes aléaoires pour cette organisation."""
        if not self.is_company:
            return False

        org_type = self.organization_type if self.organization_type else "company"
        teams = self._generate_teams_for_organization(self.id, org_type)

        self._compute_organization_counts()

        return {
            "name": f"Équipes générées pour {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "random.team",
            "view_mode": "tree,form",
            "domain": [("id", "in", [team.id for team in teams])],
        }

    @api.model
    def _generate_teams_for_organization(
        self, organization_id, organization_type="company"
    ):
        """Génère des équipes aléaoires pour une organisation."""
        team_size = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("random_team_generator.team_size", default=3)
        )

        members = self._get_members_by_type(organization_type, organization_id)

        if not members:
            return []

        member_list = list(members)
        random.shuffle(member_list)

        teams = []

        organization = self.env["res.partner"].browse(organization_id)
        existing_teams = self._get_existing_teams(organization, organization_type)
        existing_teams.unlink()

        type_names = {
            "company": "Équipe",
            "tribe": "Équipe Tribu",
            "prayer_cell": "Équipe Cellule",
            "group": "Équipe Groupe",
        }
        team_prefix = type_names.get(organization_type, "Équipe")

        for i in range(0, len(member_list), team_size):
            team_members = member_list[i : i + team_size]
            if team_members:
                team_name = f"{team_prefix} n° {len(teams) + 1}"
                team_lead = random.choice(team_members)

                team_vals = {
                    "name": team_name,
                    "members_ids": [(6, 0, [member.id for member in team_members])],
                    "team_lead_id": team_lead.id,
                    "team_type": organization_type,
                }

                if organization_type == "company":
                    team_vals["company_id"] = organization_id
                elif organization_type == "tribe":
                    team_vals["tribe_id"] = organization_id
                elif organization_type == "prayer_cell":
                    team_vals["prayer_cell_id"] = organization_id
                elif organization_type == "group":
                    team_vals["group_id"] = organization_id

                team = self.env["random.team"].sudo().create(team_vals)
                teams.append(team)

        return teams

    def _get_members_by_type(self, organization_type, organization_id):
        """Retourne les membres d'une organisation selon son type."""
        if organization_type == "company":
            return self.env["res.partner"].search(
                [("is_company", "=", False), ("church_id", "=", organization_id)]
            )
        elif organization_type == "tribe":
            direct_members = self.env["res.partner"].search(
                [("is_company", "=", False), ("tribe_id", "=", organization_id)]
            )

            prayer_cells = self.env["res.partner"].search(
                [
                    ("is_company", "=", True),
                    ("organization_type", "=", "prayer_cell"),
                    ("church_id", "=", organization_id),
                ]
            )

            cell_members = self.env["res.partner"]
            for cell in prayer_cells:
                members = self.env["res.partner"].search(
                    [("is_company", "=", False), ("prayer_cell_id", "=", cell.id)]
                )
                cell_members |= members

            all_members = direct_members | cell_members
            return all_members
        elif organization_type == "prayer_cell":
            return self.env["res.partner"].search(
                [("is_company", "=", False), ("prayer_cell_id", "=", organization_id)]
            )
        elif organization_type == "group":
            return self.env["res.partner"].search(
                [("is_company", "=", False), ("group_id", "=", organization_id)]
            )

        return self.env["res.partner"]

    def _get_existing_teams(self, organization, organization_type):
        """Retourne les équipes existantes pour une organisation."""
        domain = []

        if organization_type == "company":
            domain = [
                ("team_type", "=", "company"),
                ("company_id", "=", organization.id),
            ]
        elif organization_type == "tribe":
            domain = [("team_type", "=", "tribe"), ("tribe_id", "=", organization.id)]
        elif organization_type == "prayer_cell":
            domain = [
                ("team_type", "=", "prayer_cell"),
                ("prayer_cell_id", "=", organization.id),
            ]
        elif organization_type == "group":
            domain = [("team_type", "=", "group"), ("group_id", "=", organization.id)]

        return self.env["random.team"].search(domain)

    def action_view_teams(self):
        """Action pour afficher les équipes de cette organisation."""
        if not self.is_company:
            return False

        org_type = self.organization_type if self.organization_type else "company"
        teams = self._get_existing_teams(self, org_type)

        return {
            "name": f"Équipes de {self.name}",
            "type": "ir.actions.act_window",
            "res_model": "random.team",
            "view_mode": "tree,form",
            "domain": [("id", "in", teams.ids)],
            "context": {"default_organization_id": self.id},
        }
