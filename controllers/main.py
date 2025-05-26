from odoo import http
from odoo.http import request
from datetime import date

class ResPartnerPortal(http.Controller):

    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_my_profile(self, **kw):
        partner = request.env.user.partner_id
        return request.render('random_team_generator.portal_my_profile', {
            'partner': partner
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
                'parent_person_id': partner.id,
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
