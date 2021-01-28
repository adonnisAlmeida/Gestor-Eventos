# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
import pytz

from odoo import fields, http
from collections import OrderedDict
from odoo.http import request, route
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, consteq
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from werkzeug.exceptions import NotFound, Forbidden
from odoo.exceptions import AccessError
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

    def get_domain_my_tracks(self, user):
        return [
            '|',('reviewer_id', '=', user.id), ('reviewer2_id', '=', user.id),('stage_id', 'in', (1, 2))
        ]    
    
    def get_domain_my_new_tracks(self, user):
        return [
            ('reviewer_id', '=', user.id), ('stage_id', 'in', (1, 2)), ('recommendation','=', None)
        ]
    
    def get_domain_my_new_tracks2(self, user):
        return [
            ('reviewer2_id', '=', user.id), ('stage_id', 'in', (1, 2)), ('recommendation2','=', None)
        ]    

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        paper_count = request.env['event.track'].sudo().search_count(self.get_domain_my_papers(request.env.user))
        track_count1 = request.env['event.track'].sudo().search_count(self.get_domain_my_new_tracks(request.env.user))
        track_count2 = request.env['event.track'].sudo().search_count(self.get_domain_my_new_tracks2(request.env.user))
        track_count = track_count1 + track_count2

        registration_count = request.env['event.registration'].sudo().search_count(self.get_domain_my_registrations(request.env.user))

        values.update({
            'paper_count': paper_count,
            'revision_count': track_count,
            'registration_count': registration_count,
        })
        return values
        

    @http.route(['/my/tracks', '/my/tracks/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tracks(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Track = request.env['event.track'].sudo()
        domain = self.get_domain_my_tracks(request.env.user)

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
            'event_name': {'label': _('Event'), 'order': 'event_id'},
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
        track_count = Track.search_count(domain)
        pager = request.website.pager(
            url="/my/tracks",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=track_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        tracks = Track.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'tracks': tracks,
            'page_name': 'track',
            #'archive_groups': archive_groups,
            'default_url': '/my/tracks',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_event_track_uclv.portal_my_tracks", values)
    

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
        event_ids = request.env['event.track'].search(domain).mapped('event_id.id')
        events = request.env['event.event'].search([('website_published','=',True),('id', 'in', event_ids)])
        for event in events:
            searchbar_filters.update({
                str(event.id): {'label': event.name, 'domain': [('event_id', '=', event.id)]}
            })

        # extends filterby criteria with event (criteria name is the event id)
        event_groups = request.env['event.track'].read_group([('event_id', 'in', events.ids)],
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
        paper_count = request.env['event.track'].search_count(domain)
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

        papers = request.env['event.track'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
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
        pdf = request.env.ref('event.report_event_registration_badge').sudo().render_qweb_pdf([registration_sudo.id])[0]
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
        pdf = request.env.ref('website_event_track_uclv.report_event_registration_certificate').sudo().render_qweb_pdf([registration_sudo.id])[0]
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
    

    """@http.route(['''/my/track/<model("event.track"):track>'''], type='http', auth="user", website=True)
    def portal_my_track_slug(self, track, **post):
        track_id = track.sudo().id        
        return self.portal_my_track(track_id, **post) """

    @http.route(['''/my/track/<model("event.track"):track>'''], type='http', auth="user", website=True)
    def portal_my_track(self, track, comment_coordinator='', comment_author='', recommendation=False,**kw):
        #track = request.env['event.track'].sudo().search([('id', '=', track_id),('stage_id', 'in', (1, 2))])
        track = track.sudo()
        if not track:
            raise NotFound()
        if track.sudo().reviewer_id != request.env.user and track.sudo().reviewer2_id != request.env.user:
            raise Forbidden()
        
        if recommendation:
            if track.sudo().reviewer_id == request.env.user:
                if not track.sudo().recommendation:
                    track.sudo().write({'recommendation': recommendation})
            if track.sudo().reviewer2_id == request.env.user:
                if not track.sudo().recommendation2:
                    track.sudo().write({'recommendation2': recommendation})
        if comment_coordinator:
            if track.sudo().reviewer_id == request.env.user:
                track.sudo().write({'coordinator_notes': comment_coordinator})
            if track.sudo().reviewer2_id == request.env.user:
                track.sudo().write({'coordinator_notes2': comment_coordinator})
        if comment_author:
            if track.sudo().reviewer_id == request.env.user:
                track.sudo().write({'author_notes': comment_author})
            if track.sudo().reviewer2_id == request.env.user:
                track.sudo().write({'author_notes2': comment_author})
        
        review = False
        if track.sudo().reviewer_id == request.env.user:
            if track.sudo().recommendation == 'acceptwc':
                review = _('Accepted with changes')
            if track.sudo().recommendation == 'acceptednc':
                review = _('Accepted without changes')
            if track.sudo().recommendation == 'rejected':
                review = _('Rejected')
        if track.sudo().reviewer2_id == request.env.user:
            if track.sudo().recommendation2 == 'acceptwc':
                review = _('Accepted with changes')
            if track.sudo().recommendation2 == 'acceptednc':
                review = _('Accepted without changes')
            if track.sudo().recommendation2 == 'rejected':
                review = _('Rejected')

        return request.render("website_event_track_uclv.portal_my_track", {'track': track, 'review': review})
    

    @http.route(['''/my/paper/<model("event.track"):prop>'''], type='http', auth="user", website=True)
    def portal_my_paper(self, prop, **kw):
        prop = prop.sudo()
        if not prop:
            raise NotFound()
        if prop.sudo().partner_id != request.env.user.partner_id:
            raise Forbidden()

        for c_file in request.httprequest.files.getlist('file'):
            data = c_file.read()
            import base64
            request.env['ir.attachment'].sudo().create({
                        'name': c_file.filename,
                        'datas': base64.b64encode(data),                        
                        'public': False,
                        'res_model': 'event.track',
                        'res_id': prop.id
                    })

        return request.render(
            "website_event_track_uclv.portal_my_paper", {
                'paper': prop,
                #'user_activity': opp.activity_ids.filtered(lambda activity: activity.user_id == request.env.user)[:1],
                #'stages': request.env['crm.stage'].search([('probability', '!=', '100')], order='sequence desc'),
                #'activity_types': request.env['mail.activity.type'].sudo().search([]),
                #'states': request.env['res.country.state'].sudo().search([]),
                #'countries': request.env['res.country'].sudo().search([]),
            })
    
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
