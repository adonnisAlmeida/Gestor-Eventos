# -*- coding: utf-8 -*-

import base64

from odoo.http import content_disposition, Controller, request, route
import odoo.addons.portal.controllers.portal as PortalController


class CustomerPortal(PortalController.CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "email", "country_id", "gender"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "phone", "city", "institution", "state_id", "website_description", "street", "city", "title", "reviewer", "vat"]

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post:
            if 'image_1920' in post:
                image_1920 = post.get('image_1920')
                if image_1920:
                    image_1920 = image_1920.read()
                    image_1920 = base64.b64encode(image_1920)
                    partner.sudo().write({
                        'image_1920': image_1920
                    })
                post.pop('image_1920')
            if 'clear_avatar' in post:
                partner.sudo().write({
                    'image_1920': False
                })
                post.pop('clear_avatar')
            
            post.pop('files', None) 

            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                if not values.get('title'):
                    values.update({'title': False})
                else:
                    values.update({'title': int(values.get('title'))})
                values.update({'country_id': int(values.get('country_id'))})
                if not values.get('state_id'):
                    values.update({'state_id': False})
                else:
                    values.update({'state_id': int(values.get('state_id'))})
                values.update({'zip': values.pop('zipcode', '')})       
                                               

                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        titles = request.env['res.partner.title'].sudo().search([])
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'titles': titles,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

   