# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ChurchPrintMembersWizard(models.TransientModel):
    _name = 'church.print.members.wizard'
    _description = 'Assistant d\'impression des listes de membres'

    organization_id = fields.Many2one('res.partner', string='Organisation', required=True)
    organization_type = fields.Selection(related='organization_id.organization_type', readonly=True)
    
    # Options de filtrage
    filter_by_gender = fields.Boolean(string='Filtrer par genre')
    gender_filter = fields.Selection([
        ('male', 'Hommes seulement'),
        ('female', 'Femmes seulement')
    ], string='Genre')
    
    filter_by_age = fields.Boolean(string='Filtrer par âge')
    min_age = fields.Integer(string='Âge minimum')
    max_age = fields.Integer(string='Âge maximum')
    
    filter_by_marital_status = fields.Boolean(string='Filtrer par état civil')
    marital_status_filter = fields.Selection([
        ('single', 'Célibataires'),
        ('married', 'Mariés'),
        ('divorced', 'Divorcés'),
        ('widowed', 'Veufs/Veuves')
    ], string='État civil')
    
    include_new_members_only = fields.Boolean(string='Nouveaux membres seulement')
    include_birthday_members = fields.Boolean(string='Inclure les anniversaires du jour')
    
    # Options d'affichage
    include_phone = fields.Boolean(string='Inclure téléphone', default=True)
    include_email = fields.Boolean(string='Inclure email', default=True)
    include_profession = fields.Boolean(string='Inclure profession', default=True)
    include_address = fields.Boolean(string='Inclure adresse')
    
    # Options de tri
    sort_by = fields.Selection([
        ('name', 'Nom'),
        ('age', 'Âge'),
        ('gender', 'Genre'),
        ('arrival_date', 'Date d\'arrivée')
    ], string='Trier par', default='name')
    
    sort_order = fields.Selection([
        ('asc', 'Croissant'),
        ('desc', 'Décroissant')
    ], string='Ordre', default='asc')

    @api.multi
    def action_print_filtered_list(self):
        """
        Imprimer la liste avec les filtres appliqués
        """
        self.ensure_one()
        
        # Récupérer les membres selon le type d'organisation
        members = self._get_members()
        
        # Appliquer les filtres
        filtered_members = self._apply_filters(members)
        
        if not filtered_members:
            raise UserError("Aucun membre ne correspond aux critères sélectionnés.")
        
        # Appliquer le tri
        sorted_members = self._apply_sorting(filtered_members)
        
        # Créer un contexte avec les options d'affichage
        context = {
            'members_to_print': sorted_members.ids,
            'include_phone': self.include_phone,
            'include_email': self.include_email,
            'include_profession': self.include_profession,
            'include_address': self.include_address,
            'filter_applied': True,
        }
        
        # Retourner l'action du rapport avec le contexte
        return self.env.ref('church_management.report_members_list').with_context(context).report_action(self.organization_id)

    def _get_members(self):
        """
        Récupérer les membres selon le type d'organisation
        """
        if self.organization_type == 'company':
            return self.organization_id.company_contacts
        elif self.organization_type == 'tribe':
            return self.organization_id.tribe_members
        elif self.organization_type == 'prayer_cell':
            return self.organization_id.prayer_cell_members
        elif self.organization_type == 'group':
            return self.organization_id.group_members
        elif self.organization_type == 'communication':
            return self.organization_id.communication_members
        elif self.organization_type == 'artistic_group':
            return self.organization_id.artistic_group_members
        elif self.organization_type == 'ngo':
            return self.organization_id.ngo_members
        elif self.organization_type == 'school':
            return self.organization_id.school_members
        elif self.organization_type == 'sports_group':
            return self.organization_id.sports_group_members
        elif self.organization_type == 'educational_group':
            return self.organization_id.educational_group_members
        elif self.organization_type == 'other_group':
            return self.organization_id.other_group_members
        else:
            return self.env['res.partner']

    def _apply_filters(self, members):
        """
        Appliquer les filtres sélectionnés
        """
        filtered_members = members
        
        # Filtre par genre
        if self.filter_by_gender and self.gender_filter:
            filtered_members = filtered_members.filtered(lambda m: m.gender == self.gender_filter)
        
        # Filtre par âge
        if self.filter_by_age:
            if self.min_age:
                filtered_members = filtered_members.filtered(lambda m: m.age >= self.min_age)
            if self.max_age:
                filtered_members = filtered_members.filtered(lambda m: m.age <= self.max_age)
        
        # Filtre par état civil
        if self.filter_by_marital_status and self.marital_status_filter:
            filtered_members = filtered_members.filtered(lambda m: m.marital_status == self.marital_status_filter)
        
        # Filtre nouveaux membres
        if self.include_new_members_only:
            filtered_members = filtered_members.filtered(lambda m: m.is_new_member)
        
        # Filtre anniversaires
        if self.include_birthday_members:
            filtered_members = filtered_members.filtered(lambda m: m.is_birthday)
        
        return filtered_members

    def _apply_sorting(self, members):
        """
        Appliquer le tri sélectionné
        """
        reverse = self.sort_order == 'desc'
        
        if self.sort_by == 'name':
            return members.sorted(key=lambda m: m.name or '', reverse=reverse)
        elif self.sort_by == 'age':
            return members.sorted(key=lambda m: m.age or 0, reverse=reverse)
        elif self.sort_by == 'gender':
            return members.sorted(key=lambda m: m.gender or '', reverse=reverse)
        elif self.sort_by == 'arrival_date':
            return members.sorted(key=lambda m: m.arrival_date or fields.Date.min, reverse=reverse)
        else:
            return members.sorted(key=lambda m: m.name or '', reverse=reverse)