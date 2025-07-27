from odoo import http, fields, _
from odoo.http import request
from datetime import date
import logging
from odoo.exceptions import ValidationError, UserError  # <-- Cet import est crucial
import math
from odoo.addons.portal.controllers.portal import pager as portal_pager
import re

_logger = logging.getLogger(__name__)

class ResPartnerPortal(http.Controller):

    @http.route('/ecoles/pdf', type='http', auth="public", website=True)
    def pdf_schools(self, **post):
        schools = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'school'),
            ('active', '=', True)
        ], order='name')
        
        # Calcul des totaux
        total_monitors = sum(len(school.school_monitor_ids) for school in schools)
        total_leaders = sum(1 for school in schools if school.school_leader_id)
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'random_team_generator.school_list_pdf', 
            [0],
            data={
                'schools': schools,
                'total_monitors': total_monitors,
                'total_leaders': total_leaders,
            }
        )
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf[0])),
            ('Content-Disposition', 'attachment; filename=liste_ecoles.pdf')
        ]
        
        return request.make_response(pdf[0], headers=pdfhttpheaders)

    @http.route('/ecoles', type='http', auth="public", website=True)
    def list_schools(self, **post):
        # Récupération des paramètres de pagination
        page = int(post.get('page', 1))
        limit = int(post.get('limit', 10))  # 10 par défaut
        
        # Calcul de l'offset
        offset = (page - 1) * limit
        
        # Domaine de recherche
        domain = [
            ('organization_type', '=', 'school'),
            ('active', '=', True)
        ]
        
        # Compte total des écoles
        total_count = request.env['res.partner'].sudo().search_count(domain)
        
        # Récupération des écoles pour la page actuelle
        schools = request.env['res.partner'].sudo().search(
            domain,
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Calcul du nombre total de pages
        page_count = math.ceil(total_count / limit) if total_count > 0 else 1
        
        # Construction des URLs pour la pagination
        base_url = '/ecoles'
        
        def build_url(page_num, limit_val=limit):
            return f"{base_url}?page={page_num}&limit={limit_val}"
        
        # URLs de navigation
        url_first = build_url(1)
        url_last = build_url(page_count)
        url_previous = build_url(page - 1) if page > 1 else None
        url_next = build_url(page + 1) if page < page_count else None
        
        # Génération de la plage de pages à afficher (5 pages max)
        start_page = max(1, page - 2)
        end_page = min(page_count, page + 2)
        
        # Ajustement si on est proche du début ou de la fin
        if end_page - start_page < 4:
            if start_page == 1:
                end_page = min(page_count, start_page + 4)
            else:
                start_page = max(1, end_page - 4)
        
        page_range = list(range(start_page, end_page + 1))
        
        # Création de l'objet pager
        pager = {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'page': page,
            'page_count': page_count,
            'url_first': url_first,
            'url_last': url_last,
            'url_previous': url_previous,
            'url_next': url_next,
            'url_page': f"{base_url}?page=%s&limit={limit}",
            'page_range': page_range,
        }
        
        # Calcul des totaux pour toutes les écoles (pas seulement la page actuelle)
        all_schools = request.env['res.partner'].sudo().search(domain)
        total_monitors = sum(len(school.school_monitor_ids) for school in all_schools)
        total_leaders = sum(1 for school in all_schools if school.school_leader_id)

        return request.render("random_team_generator.school_list", {
            'schools': schools,
            'pager': pager,
            'total_monitors': total_monitors,
            'total_leaders': total_leaders
        })
    
    @http.route('/inscription-ecole', type='http', auth="public", website=True, csrf=True)
    def inscription_ecole_form(self, **post):
        """
        Formulaire d'inscription pour l'école du dimanche
        Gère l'affichage du formulaire et le traitement des données soumises
        """
        try:
            # Récupération des écoles actives
            schools = self._get_active_schools()
            
            if not schools:
                error = _("Aucune école du dimanche n'est actuellement disponible pour l'inscription.")
                return request.render("random_team_generator.inscription_ecole_form", {
                    'schools': [],
                    'error': error,
                    'values': {}
                })
            
            # Traitement de la soumission du formulaire
            if post and request.httprequest.method == 'POST':
                return self._process_form_submission(post, schools)
            
            # Affichage du formulaire vide
            return request.render("random_team_generator.inscription_ecole_form", {
                'schools': schools,
                'error': False,
                'values': {}
            })
            
        except Exception as e:
            _logger.error("Erreur inattendue dans inscription_ecole_form: %s", str(e))
            return request.render("random_team_generator.404_custom")
    
    def _get_active_schools(self):
        """Récupère la liste des écoles actives"""
        try:
            return request.env['res.partner'].sudo().search([
                ('organization_type', '=', 'school'),
                ('active', '=', True)
            ], order='name')
        except Exception as e:
            _logger.error("Erreur lors de la récupération des écoles: %s", str(e))
            return request.env['res.partner']
    
    def _process_form_submission(self, post, schools):
        """Traite la soumission du formulaire"""
        error = False
        
        try:
            # Validation et nettoyage des données
            cleaned_data = self._validate_and_clean_data(post, schools)
            
            # Vérification de doublons
            existing_partner = self._check_duplicate_registration(cleaned_data)
            if existing_partner:
                error = _("Une inscription avec ce nom et cette date de naissance existe déjà.")
                return self._render_form_with_error(schools, error, post)

            # Ajouter l'école de l'école sur le partenaire si nécessaire
            # Faire une recherche de l'école associée à l'école
            school = request.env['res.partner'].sudo().search([
                ('id', '=', cleaned_data['school_id'])
            ], limit=1)

            if school:
                cleaned_data['school_church_id'] = school.school_church_id.id if school.school_church_id else False

            # Création de l'enregistrement
            partner = self._create_partner_record(cleaned_data)
            
            # Association à l'école
            self._associate_partner_to_school(partner, cleaned_data['school_id'], cleaned_data['function_type'])
            
            # Envoi d'email de confirmation (optionnel)
            self._send_confirmation_email(partner)
            
            # Redirection vers la page de succès
            return request.render("random_team_generator.inscription_success", {
                'partner': partner,
                'school': request.env['res.partner'].sudo().browse(cleaned_data['school_id'])
            })
            
        except ValidationError as e:
            error = str(e)
            _logger.warning("Erreur de validation: %s", error)
        except UserError as e:
            error = str(e)
            _logger.warning("Erreur utilisateur: %s", error)
        except Exception as e:
            error = _("Une erreur inattendue est survenue. Veuillez réessayer plus tard.")
            _logger.error("Erreur lors de l'inscription: %s", str(e))
            # Rollback de la transaction en cas d'erreur
            try:
                request.env.cr.rollback()
            except:
                pass
        
        return self._render_form_with_error(schools, error, post)
    
    def _validate_and_clean_data(self, post, schools):
        """Valide et nettoie les données du formulaire"""
        cleaned_data = {}
        
        # Validation des champs obligatoires
        required_fields = {
            'name': 'Nom complet',
            'gender': 'Sexe', 
            'birth_day': 'Jour de naissance',
            'birth_month': 'Mois de naissance',
            'birth_year': 'Année de naissance',
            'school_id': 'École du dimanche',
            'function_type': 'Fonction',
            'accept_terms': 'Acceptation des conditions'
        }
        
        for field, label in required_fields.items():
            value = post.get(field, '').strip() if isinstance(post.get(field, ''), str) else post.get(field, '')
            if not value:
                raise ValidationError(_("Le champ '%s' est obligatoire") % label)
            cleaned_data[field] = value
        
        # Validation et construction de la date de naissance
        cleaned_data['birthdate'] = self._validate_birth_date(
            cleaned_data['birth_day'], 
            cleaned_data['birth_month'], 
            cleaned_data['birth_year']
        )
        
        # Validation de la date de salut (optionnelle)
        arrival_date = self._validate_arrival_date(
            post.get('salvation_day', ''),
            post.get('salvation_month', ''),
            post.get('salvation_year', '')
        )
        if arrival_date:
            cleaned_data['arrival_date'] = arrival_date
        
        # Validation du nom
        cleaned_data['name'] = self._validate_name(cleaned_data['name'])
        
        # Validation du sexe
        if cleaned_data['gender'] not in ['male', 'female']:
            raise ValidationError(_("Sexe invalide"))
        
        # Validation des numéros de téléphone
        cleaned_data['phone'] = self._validate_phone(post.get('phone', ''))
        cleaned_data['mobile'] = self._validate_phone(post.get('mobile', ''))
        
        # Validation de l'école
        school_id = int(cleaned_data['school_id'])
        if not schools.filtered(lambda s: s.id == school_id):
            raise ValidationError(_("École sélectionnée invalide"))
        cleaned_data['school_id'] = school_id
        
        # Validation de la fonction
        if cleaned_data['function_type'] not in ['monitor', 'teacher', 'leader']:
            raise ValidationError(_("Fonction sélectionnée invalide"))
        
        # Validation de l'acceptation des conditions
        if cleaned_data['accept_terms'] != 'on':
            raise ValidationError(_("Vous devez accepter les conditions d'utilisation"))
        
        return cleaned_data
    
    def _validate_birth_date(self, day, month, year):
        """Valide et construit la date de naissance"""
        try:
            day, month, year = int(day), int(month), int(year)
            birth_date = date(year, month, day)
            
            # Vérification de l'âge (entre 16 et 100 ans)
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 16:
                raise ValidationError(_("L'âge minimum requis est de 16 ans"))
            if age > 100:
                raise ValidationError(_("Âge invalide"))
            
            # Vérification que la date n'est pas dans le futur
            if birth_date > today:
                raise ValidationError(_("La date de naissance ne peut pas être dans le futur"))
            
            return fields.Date.to_string(birth_date)
            
        except ValueError:
            raise ValidationError(_("Date de naissance invalide"))
    
    def _validate_arrival_date(self, day, month, year):
        """Valide la date de salut (optionnelle)"""
        if not all([day, month, year]):
            return None
        
        try:
            day, month, year = int(day), int(month), int(year)
            arrival_date = date(year, month, day)
            
            # Vérification que la date n'est pas dans le futur
            if arrival_date > date.today():
                raise ValidationError(_("La date de salut ne peut pas être dans le futur"))
            
            return fields.Date.to_string(arrival_date)
            
        except ValueError:
            raise ValidationError(_("Date de salut invalide"))
    
    def _validate_name(self, name):
        """Valide et nettoie le nom"""
        if len(name) < 2:
            raise ValidationError(_("Le nom doit contenir au moins 2 caractères"))
        if len(name) > 100:
            raise ValidationError(_("Le nom ne peut pas dépasser 100 caractères"))
        
        # Nettoyage du nom (suppression des caractères spéciaux dangereux)
        cleaned_name = re.sub(r'[<>"\']', '', name)
        return cleaned_name.title()
    
    def _validate_phone(self, phone):
        """Valide le numéro de téléphone"""
        if not phone:
            return False
        
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not re.match(r'^[+]?[\d]{8,15}$', phone):
            raise ValidationError(_("Format de téléphone invalide"))
        
        return phone
    
    def _check_duplicate_registration(self, cleaned_data):
        """Vérifie s'il existe déjà une inscription similaire"""
        return request.env['res.partner'].sudo().search([
            ('name', '=', cleaned_data['name']),
            ('birthdate', '=', cleaned_data['birthdate']),
            '|', ('active', '=', True), ('active', '=', False)
        ], limit=1)
    
    def _create_partner_record(self, cleaned_data):
        """Crée l'enregistrement partner"""
        partner_vals = {
            'name': cleaned_data['name'],
            'phone': cleaned_data.get('phone') or False,
            'mobile': cleaned_data.get('mobile') or False,
            'gender': cleaned_data['gender'],
            'birthdate': cleaned_data['birthdate'],
            'arrival_date': cleaned_data.get('arrival_date') or False,
            'active': False,  # Désactivé jusqu'à validation par un admin
            'is_company': False,
            'church_id': cleaned_data.get('school_church_id') or False,
            #'supplier_rank': 0,
            #'customer_rank': 0,
            #'category_id': [(6, 0, [])],
            'comment': _("Inscription via formulaire web le %s") % fields.Datetime.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        # Ajout des champs spécifiques selon la fonction
        function_type = cleaned_data['function_type']
        if function_type == 'monitor':
            partner_vals.update({
                'is_monitor': True,
                'is_teacher': False,
                'is_leader': False
            })
        elif function_type == 'teacher':
            partner_vals.update({
                'is_monitor': False,
                'is_teacher': True,
                'is_leader': False
            })
        elif function_type == 'leader':
            partner_vals.update({
                'is_monitor': False,
                'is_teacher': False,
                'is_leader': True
            })
        
        return request.env['res.partner'].sudo().create(partner_vals)
    
    def _associate_partner_to_school(self, partner, school_id, function_type):
        """Associe le partenaire à l'école selon sa fonction"""
        school = request.env['res.partner'].sudo().browse(school_id)
        
        if not school.exists():
            raise ValidationError(_("École introuvable"))
        
        # Association selon le type de fonction
        if function_type == 'monitor':
            # Vérification que le champ existe
            if hasattr(school, 'school_monitor_ids'):
                school.write({'school_monitor_ids': [(4, partner.id)]})
        elif function_type == 'leader':
            # Vérification que le champ existe
            if hasattr(school, 'school_leader_id'):
                school.write({'school_leader_id': partner.id})
        else:
            school.write({'school_monitor_ids': [(4, partner.id)]})

    def _send_confirmation_email(self, partner):
        """Envoie un email de confirmation (optionnel)"""
        try:
            # Vérifier si un template d'email existe
            template = request.env.ref('random_team_generator.email_template_inscription_confirmation', 
                                     raise_if_not_found=False)
            if template and partner.email:
                template.sudo().send_mail(partner.id, force_send=True)
        except Exception as e:
            _logger.warning("Impossible d'envoyer l'email de confirmation: %s", str(e))
            # Ne pas faire échouer l'inscription si l'email échoue
            pass
    
    def _render_form_with_error(self, schools, error, post):
        """Rendu du formulaire avec message d'erreur"""
        return request.render("random_team_generator.inscription_ecole_form", {
            'schools': schools,
            'error': error,
            'values': post
        })
    
    @http.route('/inscription-ecole/success', type='http', auth="public", website=True)
    def inscription_success(self, **kwargs):
        """Page de confirmation d'inscription"""
        return request.render("random_team_generator.inscription_success", {})
    
    @http.route('/inscription-ecole/terms', type='http', auth="public", website=True)
    def inscription_terms(self, **kwargs):
        """Page des conditions d'utilisation"""
        return request.render("random_team_generator.inscription_terms", {})
        
    @http.route('/cellules-priere/pdf', type='http', auth="public", website=True)
    def pdf_prayer_cells(self, **post):
        prayer_cells = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'prayer_cell'),
            ('active', '=', True)
        ], order='name')
        
        # Calcul du nombre total de membres
        total_members = sum(len(cell.prayer_cell_members) for cell in prayer_cells)
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'random_team_generator.prayer_cell_list_pdf', 
            [0],
            data={
                'prayer_cells': prayer_cells,
                'total_members': total_members
            }
        )
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf[0])),
            ('Content-Disposition', 'attachment; filename=liste_cellules_priere.pdf')
        ]
        
        return request.make_response(pdf[0], headers=pdfhttpheaders)

    @http.route('/cellules-priere', type='http', auth="public", website=True)
    def list_prayer_cells(self, **post):
        # Récupération des paramètres de pagination
        page = int(post.get('page', 1))
        limit = int(post.get('limit', 10))  # 10 par défaut comme dans la version originale
        
        # Calcul de l'offset
        offset = (page - 1) * limit
        
        # Domaine de recherche
        domain = [
            ('organization_type', '=', 'prayer_cell'),
            ('active', '=', True)
        ]
        
        # Compte total des cellules de prière
        total_count = request.env['res.partner'].sudo().search_count(domain)
        
        # Récupération des cellules de prière pour la page actuelle
        prayer_cells = request.env['res.partner'].sudo().search(
            domain,
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Calcul du nombre total de pages
        page_count = math.ceil(total_count / limit) if total_count > 0 else 1
        
        # Construction des URLs pour la pagination
        base_url = '/cellules-priere'
        
        def build_url(page_num, limit_val=limit):
            return f"{base_url}?page={page_num}&limit={limit_val}"
        
        # URLs de navigation
        url_first = build_url(1)
        url_last = build_url(page_count)
        url_previous = build_url(page - 1) if page > 1 else None
        url_next = build_url(page + 1) if page < page_count else None
        
        # Génération de la plage de pages à afficher (5 pages max)
        start_page = max(1, page - 2)
        end_page = min(page_count, page + 2)
        
        # Ajustement si on est proche du début ou de la fin
        if end_page - start_page < 4:
            if start_page == 1:
                end_page = min(page_count, start_page + 4)
            else:
                start_page = max(1, end_page - 4)
        
        page_range = list(range(start_page, end_page + 1))
        
        # Création de l'objet pager
        pager = {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'page': page,
            'page_count': page_count,
            'url_first': url_first,
            'url_last': url_last,
            'url_previous': url_previous,
            'url_next': url_next,
            'url_page': f"{base_url}?page=%s&limit={limit}",
            'page_range': page_range,
        }
        
        # Calcul des statistiques globales (pour toutes les cellules de prière, pas seulement la page actuelle)
        all_prayer_cells = request.env['res.partner'].sudo().search(domain)
        
        # Calcul du nombre total de membres
        total_members = sum(len(cell.prayer_cell_members) for cell in all_prayer_cells)
        
        return request.render("random_team_generator.prayer_cell_list", {
            'prayer_cells': prayer_cells,
            'total_members': total_members,
            'pager': pager
        })

    @http.route('/eglises/pdf', type='http', auth="public", website=True)
    def pdf_churches(self, **post):
        churches = request.env['res.partner'].sudo().search([
            ('is_church', '=', True),
            ('active', '=', True)
        ], order='name')
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'random_team_generator.action_report_church_list', 
            [0],  # On passe une liste vide car nous fournissons nos propres données
            data={'churches': churches}
        )
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf[0])),
            ('Content-Disposition', 'attachment; filename=liste_eglises.pdf')
        ]
        
        return request.make_response(pdf[0], headers=pdfhttpheaders)

    @http.route('/eglises', type='http', auth="public", website=True)
    def list_churches(self, **post):
        # Récupération des paramètres de pagination
        page = int(post.get('page', 1))
        limit = int(post.get('limit', 20))  # 20 par défaut
        
        # Calcul de l'offset
        offset = (page - 1) * limit
        
        # Domaine de recherche
        domain = [
            ('is_church', '=', True),
            ('active', '=', True)
        ]
        
        # Compte total des églises
        total_count = request.env['res.partner'].sudo().search_count(domain)
        
        # Récupération des églises pour la page actuelle
        churches = request.env['res.partner'].sudo().search(
            domain,
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Calcul du nombre total de pages
        page_count = math.ceil(total_count / limit) if total_count > 0 else 1
        
        # Construction des URLs pour la pagination
        base_url = '/eglises'
        
        def build_url(page_num, limit_val=limit):
            return f"{base_url}?page={page_num}&limit={limit_val}"
        
        # URLs de navigation
        url_first = build_url(1)
        url_last = build_url(page_count)
        url_previous = build_url(page - 1) if page > 1 else None
        url_next = build_url(page + 1) if page < page_count else None
        
        # Génération de la plage de pages à afficher (5 pages max)
        start_page = max(1, page - 2)
        end_page = min(page_count, page + 2)
        
        # Ajustement si on est proche du début ou de la fin
        if end_page - start_page < 4:
            if start_page == 1:
                end_page = min(page_count, start_page + 4)
            else:
                start_page = max(1, end_page - 4)
        
        page_range = list(range(start_page, end_page + 1))
        
        # Création de l'objet pager
        pager = {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'page': page,
            'page_count': page_count,
            'url_first': url_first,
            'url_last': url_last,
            'url_previous': url_previous,
            'url_next': url_next,
            'url_page': f"{base_url}?page=%s&limit={limit}",
            'page_range': page_range,
        }
        
        # Calcul des statistiques globales (pour toutes les églises, pas seulement la page actuelle)
        all_churches = request.env['res.partner'].sudo().search(domain)
        
        # Statistiques globales
        total_regions = len(set(church.region_id.name for church in all_churches if church.region_id.name))
        total_main_pastors = len([church for church in all_churches if church.main_pastor_id.name])
        total_assistant_pastors = sum(len(church.assistant_pastor_ids) for church in all_churches)
        
        return request.render("random_team_generator.church_list", {
            'churches': churches,
            'pager': pager,
            'total_regions': total_regions,
            'total_main_pastors': total_main_pastors,
            'total_assistant_pastors': total_assistant_pastors,
        })


    @http.route('/inscription', type='http', auth="public", website=True, csrf=False)
    def inscription_complete_form(self, **post):
        # Récupération des données pour les selects
        churches = request.env['res.partner'].sudo().search([
            ('is_church', '=', True),
            ('active', '=', True)
        ])
        
        tribes = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'tribe'),
            ('active', '=', True)
        ])

        prayer_cells = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'prayer_cell'),
            ('active', '=', True)
        ])
        
        groups = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'group'),
            ('active', '=', True)
        ])
        
        # Récupération des groupes spécialisés
        communications = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'communication'),
            ('active', '=', True)
        ])
        
        artistic_groups = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'artistic_group'),
            ('active', '=', True)
        ])
        
        ngos = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'ngo'),
            ('active', '=', True)
        ])
        
        schools = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'school'),
            ('active', '=', True)
        ])
        
        sports_groups = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'sports_group'),
            ('active', '=', True)
        ])
        
        other_groups = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'other_group'),
            ('active', '=', True)
        ])

        # Initialisation de la variable error
        error = False

        if post and request.httprequest.method == 'POST':
            try:
                # Import de ValidationError dans le scope local pour éviter les problèmes d'import
                from odoo.exceptions import ValidationError
                
                if not post.get('accept_terms'):
                    raise ValidationError(_("Vous devez accepter les conditions d'utilisation"))
                
                # Validation des données obligatoires
                required_fields = ['name', 'gender', 'birth_day', 'birth_month', 'birth_year', 'marital_status', 'church_id']
                for field in required_fields:
                    if not post.get(field):
                        raise ValidationError(_("Le champ %s est obligatoire") % field)
                
                # Reconstruction de la date de naissance
                birthdate_value = False
                if post.get('birth_day') and post.get('birth_month') and post.get('birth_year'):
                    birthdate = f"{post['birth_year']}-{post['birth_month'].zfill(2)}-{post['birth_day'].zfill(2)}"
                    birthdate_value = birthdate

                # Même chose pour la date de salut
                arrival_date_value = False
                if post.get('arrival_day') and post.get('arrival_month') and post.get('arrival_year'):
                    arrival_date = f"{post['arrival_year']}-{post['arrival_month'].zfill(2)}-{post['arrival_day'].zfill(2)}"
                    arrival_date_value = arrival_date

                # Gestion des groupes spécialisés (Many2many)
                def process_multi_select(field_name):
                    ids = post.get(field_name, '').split(',') if post.get(field_name) else []
                    return [(6, 0, [int(id) for id in ids if id.isdigit()])] if ids else False

                # Préparation des valeurs
                partner_vals = {
                    'name': post.get('name'),
                    'email': post.get('email') if post.get('email') else False,
                    'phone': post.get('phone') if post.get('phone') else False,
                    'mobile': post.get('mobile') if post.get('mobile') else False,
                    'gender': post.get('gender'),
                    'birthdate': birthdate_value,
                    'marital_status': post.get('marital_status'),
                    'father_id': int(post.get('father_id')) if post.get('father_id') else False,
                    'mother_id': int(post.get('mother_id')) if post.get('mother_id') else False,
                    'church_id': int(post.get('church_id')),
                    'arrival_date': arrival_date_value,
                    'tribe_id': int(post.get('tribe_id')) if post.get('tribe_id') else False,
                    'prayer_cell_id': int(post.get('prayer_cell_id')) if post.get('prayer_cell_id') else False,
                    'group_id': int(post.get('group_id')) if post.get('group_id') else False,
                    'spouse_id': int(post.get('spouse_id')) if post.get('spouse_id') else False,
                    'function': post.get('function', ''),
                    'street2': post.get('street2', ''),
                    'tribe_type_id': int(post.get('tribe_type_id')) if post.get('tribe_type_id') else False,
                    'active': False,
                    'is_company': False,
                    'type': 'contact',
                    'comment': post.get('comment', ''),
                }
                
                # Gestion des fonctions spécifiques
                # Dans la méthode inscription_complete_form, remplacez cette partie :
                function_type = post.get('function_type')
                if function_type == 'pastor':
                    partner_vals.update({'is_pastor': True})
                elif function_type == 'elder':
                    partner_vals.update({'is_elder': True})
                elif function_type == 'deacon':
                    partner_vals.update({'is_deacon': True})
                elif function_type == 'missionary':
                    partner_vals.update({'is_missionary': True})
                elif function_type == 'leader':
                    partner_vals.update({'is_leader': True})

                # Par cette nouvelle version qui gère plusieurs fonctions :
                function_types = post.get('function_types', '').split(',') if post.get('function_types') else []
                partner_vals.update({
                    'is_pastor': 'pastor' in function_types,
                    'is_elder': 'elder' in function_types,
                    'is_deacon': 'deacon' in function_types,
                    'is_missionary': 'missionary' in function_types,
                    'is_leader': 'leader' in function_types,
                })
                
                # Création du partenaire
                partner = request.env['res.partner'].sudo().create(partner_vals)
                
                # Gestion des relations Many2many après la création
                m2m_fields = {
                    'communication_ids': communications,
                    'artistic_group_ids': artistic_groups,
                    'ngo_ids': ngos,
                    'school_ids': schools,
                    'sports_group_ids': sports_groups,
                    'other_group_ids': other_groups
                }
                
                for field_name, records in m2m_fields.items():
                    ids = post.get(field_name, '').split(',') if post.get(field_name) else []
                    if ids:
                        valid_ids = [int(id) for id in ids if id.isdigit() and int(id) in records.ids]
                        partner.write({field_name: [(6, 0, valid_ids)]})
                
                # Assignation automatique au groupe d'âge si pertinent
                if partner.birthdate:
                    partner._assign_age_group()
                
                return request.render("random_team_generator.inscription_success", {
                    'partner': partner
                })
                
            except ValidationError as e:
                error = str(e)
            except Exception as e:
                error = _("Une erreur est survenue lors de l'inscription : %s") % str(e)
                _logger.error("Erreur inscription: %s", str(e))
                # Rollback de la transaction en cas d'erreur
                try:
                    request.env.cr.rollback()
                except:
                    pass
        
        return request.render("random_team_generator.inscription_form", {
            'churches': churches,
            'tribes': tribes,
            'prayer_cells': prayer_cells,
            'groups': groups,
            'communications': communications,
            'artistic_groups': artistic_groups,
            'ngos': ngos,
            'schools': schools,
            'sports_groups': sports_groups,
            'other_groups': other_groups,
            'error': error,
            'values': post
        })


    @http.route('/my/fathered-children', type='http', auth='user', website=True)
    def portal_fathered_children(self):
        partner = request.env.user.partner_id
        children = partner.children_from_father_ids
        return request.render('random_team_generator.portal_fathered_children', {
            'children': children
        })

    @http.route('/my/mothered-children', type='http', auth='user', website=True)
    def portal_mothered_children(self):
        partner = request.env.user.partner_id
        children = partner.children_from_mother_ids
        return request.render('random_team_generator.portal_mothered_children', {
            'children': children
        })

    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_my_profile(self, **kw):
        partner = request.env.user.partner_id
        return request.render('random_team_generator.portal_my_profile', {
            'partner': partner,
            'error': {},
            'error_message': []
        })

    @http.route(['/my/profile/update'], type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def portal_my_profile_update(self, **post):
        partner = request.env.user.partner_id
        error = {}
        error_message = []
        values = {}  # Initialisation de la variable values au début

        # Validation des données
        if not post.get('name'):
            error['name'] = 'missing'
            error_message.append('Le nom est obligatoire')
        
        birthdate = post.get('birthdate')
        if birthdate:
            try:
                # Convertir la date du format HTML (YYYY-MM-DD) en format Odoo
                birthdate_dt = fields.Date.from_string(birthdate)
                values['birthdate'] = birthdate_dt
            except ValueError:
                error['birthdate'] = 'invalid'
                error_message.append('Date de naissance invalide - Format attendu: AAAA-MM-JJ')
            except Exception as e:
                error['birthdate'] = 'invalid'
                error_message.append(f'Erreur de traitement de la date: {str(e)}')
        
        arrival_date_str = post.get('arrival_date')
        if arrival_date_str:
            try:
                arrival_date = fields.Date.from_string(arrival_date_str)
                values['arrival_date'] = arrival_date
            except ValueError:
                error['arrival_date'] = 'invalid'
                error_message.append('Date de salut invalide - Format attendu: AAAA-MM-JJ')
            except Exception:
                error['arrival_date'] = 'invalid'
                error_message.append("Date de salut invalide.")
        if not error:
            # Mise à jour des valeurs seulement si pas d'erreur
            values.update({
                'name': post.get('name'),
                'gender': post.get('gender'),
                'marital_status': post.get('marital_status'),
                'spouse_id': int(post.get('spouse_id')) if post.get('spouse_id') else False,
            })
            
            partner.sudo().write(values)
            return request.redirect('/my/profile')
        
        return request.render('random_team_generator.portal_my_profile', {
            'partner': partner,
            'error': error,
            'error_message': error_message,
        })

    @http.route(['/my/contacts'], type='http', auth='user', website=True)
    def portal_contacts(self, **kw):
        partner = request.env.user.partner_id
        children = partner.children_ids
        return request.render('random_team_generator.portal_contact_list', {
            'partner': partner,
            'children': children,
        })

    @http.route(['/my/contacts/new'], type='http', auth='user', website=True, csrf=False)
    def portal_contact_create(self, **post):
        if post:
            partner = request.env.user.partner_id
            request.env['res.partner'].sudo().create({
                'name': post.get('name'),
                'father_id': partner.id if post.get('father_id') else False,
                'mother_id': partner.id if post.get('mother_id') else False,
                'gender': post.get('gender'),
                'birthdate': post.get('birthdate'),
                'marital_status': post.get('marital_status'),
            })
            return request.redirect('/my/contacts')
        return request.render('random_team_generator.portal_contact_form', {'create': True})

    @http.route(['/my/contacts/<int:contact_id>/edit'], type='http', auth='user', website=True, csrf=False)
    def portal_contact_edit(self, contact_id, **post):
        contact = request.env['res.partner'].sudo().browse(contact_id)
        if post:
            contact.write({
                'name': post.get('name'),
                'gender': post.get('gender'),
                'birthdate': post.get('birthdate'),
                'marital_status': post.get('marital_status'),
            })
            return request.redirect('/my/contacts')
        return request.render('random_team_generator.portal_contact_form', {
            'contact': contact,
            'create': False
        })

    @http.route(['/my/contacts/<int:contact_id>/delete'], type='http', auth='user', website=True)
    def portal_contact_delete(self, contact_id, **kw):
        contact = request.env['res.partner'].sudo().browse(contact_id)
        contact.unlink()
        return request.redirect('/my/contacts')