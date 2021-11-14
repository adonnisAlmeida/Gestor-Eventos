# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
import pytz
import uuid

from odoo import fields, http
from collections import OrderedDict
from odoo.http import request, route
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, consteq
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from werkzeug.exceptions import NotFound, Forbidden, InternalServerError
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


class PortalController(CustomerPortal):
    
    def get_domain_my_papers(self, user):
        return [
            ('partner_id', '=', user.partner_id.id)
        ]

    def get_domain_my_registrations(self, user):
        return [
            ('partner_id', '=', user.partner_id.id)
        ]

    def get_domain_my_reviews(self, user):
        return [
            ('partner_id', '=', user.partner_id.id)
        ]    
    
    def get_domain_my_new_reviews(self, user):
        return [
            ('partner_id', '=', user.partner_id.id), ('state', 'in', ('notice','read'))
        ]    
     

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        paper_count = request.env['event.track'].sudo().search_count(self.get_domain_my_papers(request.env.user))
        all_review_count = request.env['event.track.review'].sudo().search_count(self.get_domain_my_reviews(request.env.user))        
        new_review_count = request.env['event.track.review'].sudo().search_count(self.get_domain_my_new_reviews(request.env.user))

        #registration_count = request.env['event.registration'].sudo().search_count(self.get_domain_my_registrations(request.env.user))

        values.update({
            'paper_count': paper_count,
            'new_review_count': new_review_count,
            'all_review_count': all_review_count,
            #'registration_count': registration_count,
        })
        return values
        

    @http.route(['/my/papers', '/my/papers/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_papers(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id, event_id'},
            'event': {'label': _('Event'), 'order': 'event_id, stage_id'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search in Content</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},            
            'stage': {'input': 'stage', 'label': _('Search in Stages')},
            'event': {'input': 'project', 'label': _('Search in Event')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'event': {'input': 'event', 'label': _('Event')},
            'stage': {'input': 'stage', 'label': _('Stage')},
        }

        # extends filterby criteria with event the customer has access to
        domain = self.get_domain_my_papers(request.env.user)
        event_ids = request.env['event.track'].sudo().search(domain).mapped('event_id.id')
        events = request.env['event.event'].sudo().search([('website_published','=',True),('id', 'in', event_ids)])
        for event in events:
            searchbar_filters.update({
                str(event.id): {'label': event.name, 'domain': [('event_id', '=', event.id)]}
            })

        # extends filterby criteria with event (criteria name is the event id)
        event_groups = request.env['event.track'].sudo().read_group([('event_id', 'in', events.ids)],
                                                                ['event_id'], ['event_id'])
        for group in event_groups:
            ev_id = group['event_id'][0] if group['event_id'] else False
            ev_name = group['event_id'][1] if group['event_id'] else _('Others')
            searchbar_filters.update({
                str(ev_id): {'label': ev_name, 'domain': [('event_id', '=', ev_id)]}
            })

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'all'        
        domain += searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

        # default group by value
        if not groupby:
            groupby = 'event'

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            if search_in in ('event', 'all'):
                search_domain = OR([search_domain, [('event_id', 'ilike', search)]])
            domain += search_domain

        # paper count
        paper_count = request.env['event.track'].sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/papers",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=paper_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        if groupby == 'event':
            order = "event_id, %s" % order  # force sort on event first to group by event in view
        elif groupby == 'stage':
            order = "stage_id, %s" % order  # force sort on stage first to group by stage in view

        papers = request.env['event.track'].sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_paper_history'] = papers.ids[:100]

        if groupby == 'event':
            grouped_papers = [request.env['event.track'].concat(*g) for k, g in groupbyelem(papers, itemgetter('event_id'))]
        elif groupby == 'stage':
            grouped_papers = [request.env['event.track'].concat(*g) for k, g in groupbyelem(papers, itemgetter('stage_id'))]
        else:
            grouped_papers = [papers]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_papers': grouped_papers,
            'page_name': 'paper',
            'default_url': '/my/papers',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })        
        return request.render("website_event_track_uclv.portal_my_papers", values)
    
    @http.route(['''/my/paper/<int:track_id>'''], type='http', auth="public", website=True)
    def portal_my_paper(self, track_id, access_token=None, **kw):
        if access_token:
            try:
                prop = self._document_check_access('event.track', track_id, access_token=access_token)
                prop = prop.sudo()
            except (AccessError, MissingError):
                return request.redirect('/my')
        else:
            # no access token but user may still be authorized cause it's the partner of the review
            prop = request.env['event.track'].sudo().browse(track_id)
            if prop.partner_id != request.env.user.partner_id:
                raise Forbidden()
        
        if not prop:
            raise NotFound()        

        for c_file in request.httprequest.files.getlist('file'):
            data = c_file.read()            
            request.env['ir.attachment'].sudo().create({
                        'name': c_file.filename,
                        'raw': data,
                        'public': False,
                        'res_model': 'event.track',
                        'res_id': prop.id
                    })

        return request.render(
            "website_event_track_uclv.portal_my_paper", {
                'paper': prop                
            })

    @http.route(['/my/reviews', '/my/reviews/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_reviews(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'state': {'label': _('State'), 'order': 'state, event_id'},
            'event': {'label': _('Event'), 'order': 'event_id, state'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search in Content</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'event': {'input': 'project', 'label': _('Search in Event')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'event': {'input': 'event', 'label': _('Event')},
            'state': {'input': 'state', 'label': _('State')},
        }

        # extends filterby criteria with event the customer has access to
        domain = self.get_domain_my_reviews(request.env.user)
        event_ids = request.env['event.track.review'].sudo().search(domain).mapped('track_id.event_id.id')
        events = request.env['event.event'].sudo().search([('website_published','=',True),('id', 'in', event_ids)])
        for event in events:
            searchbar_filters.update({
                str(event.id): {'label': event.name, 'domain': [('event_id', '=', event.id)]}
            })

        # extends filterby criteria with event (criteria name is the event id)
        event_groups = request.env['event.track'].sudo().read_group([('event_id', 'in', events.ids)],
                                                                ['event_id'], ['event_id'])
        for group in event_groups:
            ev_id = group['event_id'][0] if group['event_id'] else False
            ev_name = group['event_id'][1] if group['event_id'] else _('Others')
            searchbar_filters.update({
                str(ev_id): {'label': ev_name, 'domain': [('event_id', '=', ev_id)]}
            })

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'all'        
        domain += searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

        # default group by value
        if not groupby:
            groupby = 'event'

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', '|', ('name', 'ilike', search), ('description', 'ilike', search), ('description_es', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            #if search_in in ('stage', 'all'):
            #    search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            if search_in in ('event', 'all'):
                search_domain = OR([search_domain, [('event_id', 'ilike', search)]])
            domain += search_domain

        # review count
        review_count = request.env['event.track.review'].sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/reviews",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=review_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        if groupby == 'event':
            order = "event_id, %s" % order  # force sort on event first to group by event in view
        elif groupby == 'state':
            order = "state, %s" % order  # force sort on status first to group by status in view

        reviews = request.env['event.track.review'].sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_review_history'] = reviews.ids[:100]

        if groupby == 'event':
            grouped_reviews = [request.env['event.track.review'].concat(*g) for k, g in groupbyelem(reviews, itemgetter('event_id'))]
        elif groupby == 'status':
            grouped_reviews = [request.env['event.track.review'].concat(*g) for k, g in groupbyelem(reviews, itemgetter('state'))]
        else:
            grouped_reviews = [reviews]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_reviews': grouped_reviews,
            'page_name': 'review',
            'default_url': '/my/reviews',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })        
        return request.render("website_event_track_uclv.portal_my_reviews", values)
    

    @http.route(['''/my/review/<int:review_id>'''], type='http', auth="public", website=True)
    def portal_my_review(self, review_id, access_token=None, comment_manager='', comment_author='', recommendation=False,**kw):        
        if access_token:
            try:
                review = self._document_check_access('event.track.review', review_id, access_token=access_token)
                review = review.sudo()
            except (AccessError, MissingError):
                return request.redirect('/my')
        else:
            # no access token but user may still be authorized cause it's the partner of the review
            review = request.env['event.track.review'].sudo().browse(review_id)
            if review.partner_id != request.env.user.partner_id:
                raise Forbidden()
        
        if not review:
            raise NotFound()
        
        message = ''
        if review.state == 'notice':
            review.write({'state': 'read'}) #the reviewer has seen the paper
        
        if not review.expired and review.track_id.stage_id.can_review:
            if recommendation:
                review.write({'state': recommendation})
                message = 'review_ok'
            
        """if comment_manager:
            if paper.reviewer_id == request.env.user:
                paper.write({'manager_notes': comment_manager})
            if paper.reviewer2_id == request.env.user:
                paper.write({'manager_notes2': comment_manager})
        if comment_author:
            if paper.reviewer_id == request.env.user:
                paper.write({'author_notes': comment_author})
            if paper.reviewer2_id == request.env.user:
                paper.write({'author_notes2': comment_author})
        
        review = False
        if paper.reviewer_id == request.env.user:
            if paper.recommendation == 'acceptwc':
                review = _('Accepted with changes')
            if paper.recommendation == 'acceptednc':
                review = _('Accepted without changes')
            if paper.recommendation == 'rejected':
                review = _('Rejected')
        if paper.reviewer2_id == request.env.user:
            if paper.recommendation2 == 'acceptwc':
                review = _('Accepted with changes')
            if paper.recommendation2 == 'acceptednc':
                review = _('Accepted without changes')
            if paper.recommendation2 == 'rejected':
                review = _('Rejected')"""

        return request.render("website_event_track_uclv.portal_my_review", {'review': review, 'message': message})
    

    





    def _registration_check_access(self, registration_id, access_token=None):
        registration = request.env['event.registration'].browse([registration_id])
        registration_sudo = registration.sudo()
        try:
            registration.check_access_rights('read')
            registration.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(registration_sudo.access_token, access_token):
                raise
        return registration_sudo

    @http.route(['/my/registrations/pdf/<int:registration_id>'], type='http', auth="user", website=True)
    def portal_my_registration_report(self, registration_id, access_token=None, **kw):
        try:
            registration_sudo = self._registration_check_access(registration_id, access_token)
        except AccessError:
            return request.redirect('/my')
        
        if registration_sudo.state == 'cancel':
            raise Forbidden()
            
        # print report as sudo, since it require access to taxes, payment term, ... and portal
        # does not have those access rights.
        pdf = request.env.ref('event.report_event_registration_badge').sudo()._render_qweb_pdf([registration_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/registrations/certificate/<int:registration_id>'], type='http', auth="user", website=True)
    def portal_my_registration_certificate_report(self, registration_id, access_token=None, **kw):
        try:
            registration_sudo = self._registration_check_access(registration_id, access_token)
        except AccessError:
            return request.redirect('/my')
        
        if registration_sudo.state != 'done':
            raise Forbidden()
            
        # does not have those access rights.
        pdf = request.env.ref('website_event_track_uclv.report_event_registration_certificate').sudo()._render_qweb_pdf([registration_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route(['/my/registrations/cancel'], type='http', auth="user", method="post", website=True)
    def portal_my_registration_cancel(self, registration_id, **post):
        registration = request.env['event.registration'].sudo().search([('id', '=', registration_id)])
        if registration:
            if registration.partner_id != request.env.user.partner_id:
                raise Forbidden()

            registration.write({'state': 'cancel'})
            return request.redirect('/my/registration/'+str(registration_id))
        else:
            raise NotFound()

    @http.route(['/my/registrations', '/my/registrations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_registrations(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        Registration = request.env['event.registration']
        domain = self.get_domain_my_registrations(request.env.user)

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'event': {'label': _('Event'), 'order': 'event_id'},
            'ticket': {'label': _('Ticket'), 'order': 'event_ticket_id'},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # archive groups - Default Group By 'create_date'
        #archive_groups = self._get_archive_groups('event.track', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # pager
        registrations_count = Registration.search_count(domain)
        pager = request.website.pager(
            url="/my/registrations",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=registrations_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        registrations = Registration.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'registrations': registrations,
            'page_name': 'registrations',
            #'archive_groups': archive_groups,
            'default_url': '/my/registrations',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("website_event_track_uclv.portal_my_registrations", values)
    
    @http.route(['''/my/registration/<model("event.registration"):reg>'''], type='http', auth="user", website=True)
    def portal_my_registration(self, reg, **kw):
        reg = reg.sudo()
        if not reg:
            raise NotFound()
        if reg.partner_id != request.env.user.partner_id:
            raise Forbidden()

        return request.render(
            "website_event_track_uclv.portal_my_registration", {
                'registration': reg,
                #'user_activity': opp.activity_ids.filtered(lambda activity: activity.user_id == request.env.user)[:1],
                #'stages': request.env['crm.stage'].search([('probability', '!=', '100')], order='sequence desc'),
                #'activity_types': request.env['mail.activity.type'].sudo().search([]),
                #'states': request.env['res.country.state'].sudo().search([]),
                #'countries': request.env['res.country'].sudo().search([]),
            })

    @http.route(['''/event/checkpoint/<int:reg_id>'''], type='http', auth="user", website=True)
    def event_checkpoint(self, reg_id, **kw):
        user = request.env.user
        group = request.env.ref("event.group_event_manager")
        if group not in user.groups_id:
            raise Forbidden()
        reg = request.env['event.registration'].sudo().search([('id', '=', reg_id)])
        
        return request.render(
            "website_event_track_uclv.event_checkpoint", {
                'registration': reg
            })

    @http.route(['''/build_access_tokens'''], type='http', auth="user", website=True)
    def build_access_tokens(self, **kw):
        user = request.env.user
        group = request.env.ref("event.group_event_manager")
        if group not in user.groups_id:
            raise Forbidden()
        
        att = request.env['ir.attachment'].search([('res_model', '=', 'event.track'),('access_token','=', False),('public','=',False)])
        att.generate_access_token()

        return request.redirect('/events')

    @http.route(['/my/tracks/certificate/<int:track_id>', '/tracks/certificate/<int:track_id>'], type='http', auth="user", website=True)
    def portal_my_track_certificate_report(self, track_id, access_token=None, **kw):
        try:
            track_sudo = self._document_check_access('event.track', track_id, access_token=access_token)
        except AccessError:
            return request.redirect('/my')
        
        if track_sudo.stage_id.id not in (3, 4):
            raise NotFound()
            
        # does not have those access rights.
        pdf = request.env.ref('website_event_track_uclv.report_event_track_certificate').sudo()._render_qweb_pdf([track_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)