# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteEventSaleUCLVController(WebsiteEventSaleController):

    @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def event_register(self, event, **post):
        event = event.with_context(pricelist=request.website.get_current_pricelist().id)
        return super(WebsiteEventSaleUCLVController, self).event_register(event, **post)

    def _process_tickets_details(self, data):
        ticket_post = {}
        for key, value in data.items():
            if not key.startswith('nb_register') or '-' not in key:
                continue
            items = key.split('-')
            if len(items) < 2:
                continue
            ticket_post[int(items[1])] = int(value)
        tickets = request.env['event.event.ticket'].browse(tuple(ticket_post))
        return [{'id': ticket.id, 'name': ticket.name, 'quantity': ticket_post[ticket.id], 'price': ticket.price} for ticket in tickets if ticket_post[ticket.id]]

    """@http.route(['/event/<model("event.event"):event>/registration/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        try:
            order = request.website.sale_get_order(force_create=1)
            attendee_ids = set()

            registrations = self._process_registration_details(post)
            for registration in registrations:
                ticket = request.env['event.event.ticket'].sudo().browse(int(registration['ticket_id']))
                cart_values = order.with_context(event_ticket_id=ticket.id, fixed_price=True)._cart_update(product_id=ticket.product_id.id, add_qty=1, registration_data=[registration])
                attendee_ids |= set(cart_values.get('attendee_ids', []))

            # free tickets -> order with amount = 0: auto-confirm, no checkout
            #if not order.amount_total:
            order.action_confirm()  # tde notsure: email sending ?
            attendees = request.env['event.registration'].browse(list(attendee_ids))
            # clean context and session, then redirect to the confirmation page
            request.website.sale_reset()
            return request.render("website_event.registration_complete", {
                'attendees': attendees,
                'event': event,
            })
        except ValidationError as e:
            #order.unlink()
            request.website.sale_reset()
            return request.render("website_event_uclv.registration_error", {
                'error': e.name,
            })

        return request.redirect("/shop/checkout")
    """

    def _process_registration_details(self, details):        
        ''' Process data posted from the attendee details form. '''
        registrations = {}
        global_values = {}
        for key, value in details.items():
            counter, field_name = key.split('-', 1)
            if counter == '0':
                global_values[field_name] = value
            else:
                registrations.setdefault(counter, dict())[field_name] = value
        for key, value in global_values.items():
            for registration in registrations.values():
                registration[key] = value
        return list(registrations.values())
    
    @http.route(['/event/<model("event.event"):event>/registration/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        try:
            Attendees = request.env['event.registration']
            registrations = self._process_registration_details(post)

            for registration in registrations:
                registration['event_id'] = event
                registration['event_ticket_id'] = registration.get('ticket_id', None)
                registration['currency_id'] = request.website.get_current_pricelist().currency_id.id
                Attendees += Attendees.sudo().create(
                    Attendees._prepare_attendee_values(registration))

            return request.render("website_event.registration_complete", {
                'attendees': Attendees,
                'event': event,
            })
        except ValidationError as e:
            request.website.sale_reset()
            return request.render("website_event_uclv.registration_error", {
                'error': e.name,
                'event': event
            })
    

    def _add_event(self, event_name="New Event", context=None, **kwargs):
        product = request.env.ref('event_sale.product_product_event', raise_if_not_found=False)
        if product:
            context = dict(context or {}, default_event_ticket_ids=[[0, 0, {
                'name': _('Registration'),
                'product_id': product.id,
                'deadline': False,
                'seats_max': 1000,
                'price': 0,
            }]])
        return super(WebsiteEventSaleUCLVController, self)._add_event(event_name, context, **kwargs)


class WebsiteEventSaleUCLVShopController(WebsiteSale):
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        #return request.render("website.404")
        return request.redirect('/event')
