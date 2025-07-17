from odoo import http, fields, _
from odoo.http import request
from datetime import date
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class ResPartnerPortal(http.Controller):
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
        prayer_cells = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'prayer_cell'),
            ('active', '=', True)
        ], order='name')
        
        # Calcul du nombre total de membres
        total_members = sum(len(cell.prayer_cell_members) for cell in prayer_cells)
        
        return request.render("random_team_generator.prayer_cell_list", {
            'prayer_cells': prayer_cells,
            'total_members': total_members
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
        churches = request.env['res.partner'].sudo().search([
            ('is_church', '=', True),
            ('active', '=', True)
        ], order='name')
        
        return request.render("random_team_generator.church_list", {
            'churches': churches
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
        
        academies = request.env['res.partner'].sudo().search([
            ('organization_type', '=', 'academy'),
            ('active', '=', True)
        ])
        
        existing_members = request.env['res.partner'].sudo().search([
            ('is_company', '=', False),
            ('active', '=', True)
        ], limit=100)  # Limite pour des raisons de performance
        
        if post and request.httprequest.method == 'POST':
            try:
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

                # Préparation des valeurs
                partner_vals = {
                    'name': post.get('name'),
                    'email': post.get('email') if post.get('email') else False,
                    'phone': post.get('phone') if post.get('phone') else False,
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
                    'academy_id': int(post.get('academy_id')) if post.get('academy_id') else False,
                    'spouse_id': int(post.get('spouse_id')) if post.get('spouse_id') else False,
                    'function': post.get('function', ''),
                    'street2': post.get('street2', ''),
                    'active': False,  # Inactif jusqu'à validation
                    'is_company': False,
                    'type': 'contact',
                    'comment': post.get('comment', ''),
                }
                
                # Gestion des fonctions spécifiques
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
                
                # Création du partenaire
                partner = request.env['res.partner'].sudo().create(partner_vals)
                
                # Assignation automatique au groupe d'âge si pertinent
                if partner.birthdate:
                    partner._assign_age_group()
                
                return request.render("random_team_generator.inscription_success", {
                    'partner': partner
                })
                
            except ValidationError as e:
                error = e
            except Exception as e:
                error = _("Une erreur est survenue lors de l'inscription : %s") % str(e)
                request.env.cr.rollback()
        else:
            error = False
        
        return request.render("random_team_generator.inscription_form", {
            'churches': churches,
            'tribes': tribes,
            'prayer_cells': prayer_cells,
            'groups': groups,
            'academies': academies,
            'existing_members': existing_members,
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