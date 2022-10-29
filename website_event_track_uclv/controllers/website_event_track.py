# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
from pytz import timezone, utc
import json

from odoo import fields, http
from collections import OrderedDict
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, plaintext2html, is_html_empty
from odoo.addons.website_event_track.controllers.event_track import EventTrackController
from werkzeug.exceptions import NotFound, Forbidden
from langdetect import detect
from odoo.osv import expression


class UCLVWebsiteEventTrackController(EventTrackController):
    def _get_event_tracks_base_domain(self, event):
        """ Base domain for displaying tracks. Restrict to accepted or published
        tracks for people not managing events. Unpublished tracks may be displayed
        but not reachable for teasing purpose. """
        search_domain_base = [
            ('event_id', '=', event.id),
        ]
        if request.env.user.has_group('event.group_event_manager'):
            search_domain_base = [('event_id', '=', event.id)]
        elif request.env.user.has_group('event.group_event_user'):
            search_domain_base = expression.AND([
                search_domain_base,
                ['|', ('website_published', '=', True), ('user_id', '=', request.env.user.id)]
            ])
        else:
            search_domain_base = expression.AND([
                search_domain_base,
                [('website_published', '=', True)]
            ])
        return search_domain_base

    @http.route([
        '''/event/<model("event.event"):event>/track''',
        '''/event/<model("event.event"):event>/track/tag/<model("event.track.tag"):tag>'''
    ], type='http', auth="public", website=True, sitemap=False)
    def event_tracks(self, event, tag=None, **searches):
        """ Main route

        :param event: event whose tracks are about to be displayed;
        :param tag: deprecated: search for a specific tag
        :param searches: frontend search dict, containing

          * 'search': search string;
          * 'tags': list of tag IDs for filtering;
        """
        if not event.can_access_from_current_website():
            raise NotFound()

        return request.render(
            "website_event_track.tracks_session",
            self._event_tracks_get_values(event, tag=tag, **searches)
        )

    def _event_tracks_get_values(self, event, tag=None, **searches):
        # init and process search terms
        searches.setdefault('search', '')
        searches.setdefault('search_wishlist', '')
        searches.setdefault('tags', '')
        search_domain = self._get_event_tracks_base_domain(event)

        # search on content
        if searches.get('search'):
            search_domain = expression.AND([
                search_domain,
                [('name', 'ilike', searches['search'])]
            ])

        # search on tags
        search_tags = self._get_search_tags(searches['tags'])
        #if not search_tags and tag:  # backward compatibility
        #    search_tags = tag
        if search_tags:
            # Example: You filter on age: 10-12 and activity: football.
            # Doing it this way allows to only get events who are tagged "age: 10-12" AND "activity: football".
            # Add another tag "age: 12-15" to the search and it would fetch the ones who are tagged:
            # ("age: 10-12" OR "age: 12-15") AND "activity: football
            grouped_tags = dict()
            for search_tag in search_tags:
                grouped_tags.setdefault(search_tag.category_id, list()).append(search_tag)
            search_domain_items = [
                [('tag_ids', 'in', [tag.id for tag in grouped_tags[group]])]
                for group in grouped_tags
            ]
            search_domain = expression.AND([
                search_domain,
                *search_domain_items
            ])

        # fetch data to display with TZ set for both event and tracks
        now_tz = utc.localize(fields.Datetime.now().replace(microsecond=0), is_dst=False).astimezone(timezone(event.date_tz))
        today_tz = now_tz.date()
        event = event.with_context(tz=event.date_tz or 'UTC')
        tracks_sudo = event.env['event.track'].sudo().search(search_domain, order='date asc')
        tag_categories = request.env['event.track.tag.category'].sudo().search([])

        # filter on wishlist (as post processing due to costly search on is_reminder_on)
        if searches.get('search_wishlist'):
            tracks_sudo = tracks_sudo.filtered(lambda track: track.is_reminder_on)

        # organize categories for display: announced, live, soon and day-based
        tracks_announced = tracks_sudo.filtered(lambda track: not track.date)
        tracks_wdate = tracks_sudo - tracks_announced
        date_begin_tz_all = list(set(
            dt.date()
            for dt in self._get_dt_in_event_tz(tracks_wdate.mapped('date'), event)
        ))
        date_begin_tz_all.sort()
        tracks_sudo_live = tracks_wdate.filtered(lambda track: track.is_published and track.is_track_live)
        tracks_sudo_soon = tracks_wdate.filtered(lambda track: track.is_published and not track.is_track_live and track.is_track_soon)
        tracks_by_day = []
        for display_date in date_begin_tz_all:
            matching_tracks = tracks_wdate.filtered(lambda track: self._get_dt_in_event_tz([track.date], event)[0].date() == display_date)
            tracks_by_day.append({'date': display_date, 'name': display_date, 'tracks': matching_tracks})
        if tracks_announced:
            tracks_announced = tracks_announced.sorted('wishlisted_by_default', reverse=True)
            tracks_by_day.append({'date': False, 'name': _('Coming soon'), 'tracks': tracks_announced})

        # return rendering values
        return {
            # event information
            'event': event,
            'main_object': event,
            # tracks display information
            'tracks': tracks_sudo,
            'tracks_by_day': tracks_by_day,
            'tracks_live': tracks_sudo_live,
            'tracks_soon': tracks_sudo_soon,
            'today_tz': today_tz,
            # search information
            'searches': searches,
            'search_key': searches['search'],
            'search_wishlist': searches['search_wishlist'],
            'search_tags': search_tags,
            'tag_categories': tag_categories,
            # environment
            'is_html_empty': is_html_empty,
            'hostname': request.httprequest.host.split(':')[0],
            'user_event_manager': request.env.user.has_group('event.group_event_user'),
        }

    @http.route(['/buildchats'], type='http', auth="public", website=True)
    def event_track_build_chat(self, **kw):
        tracks = request.env['event.track'].sudo().search([('track_chat_id','=',False)])
        for track in tracks:
            chat = request.env['event.track.chat'].sudo().create({})
            track.write({'track_chat_id': chat.id})
        
        return request.redirect('/event')

    @http.route(['/event/<model("event.event"):event>/track_proposal'], type='http', auth="user", methods=['GET', 'POST'], website=True)
    def event_track_proposal(self, event, **post):        
        if not event.can_access_from_current_website():
            raise NotFound()
        countries = request.env['res.country'].sudo().search([])
        error = {}
        if not post:
            return request.render("website_event_track.event_track_proposal", {'event': event, 'countries': countries, 'main_object': event, 'error': error})

        if not event.website_track_proposal or event.paper_abstract_deadline_overdue or event.is_done:
            return request.render("website_event_track.event_track_proposal", {'event': event, 'countries': countries, 'main_object': event, 'error': error})

        
        language_id = post.get('language_id', False)        
        if not language_id:
            error.update({'language_id': _('Language is required')})
        else:
            try:
                language_id = int(language_id)
                if language_id not in event.allowed_language_ids.mapped('id'):
                    error.update({'language_id': _('Language not allowed')})
            except ValueError:
                error.update({'language_id': _('Language not allowed')})              
            
        
        track_name =  post.get('track_name', '')        
        if not track_name:
            error.update({'track_name': _('Title is required')})
        else:
            track_name = track_name.strip().rstrip()
            if not track_name:
                error.update({'track_name': _('Title is invalid')})

        track_name_es =  post.get('track_name_es', '')
        if not track_name_es:
            error.update({'track_name_es': _('Title is required')})
        else:
            track_name_es = track_name_es.strip().rstrip()
            if not track_name_es:
                error.update({'track_name_es': _('Title is invalid')})

        description =  post.get('description', '')
        if not description:
            error.update({'description': _('Abstract is required')})
        else:
            try:
                description_text = html2plaintext(description)
                description_text = description_text.replace('  ', ' ')            
                if len(description_text.split(' ')) < 50:
                    error.update({'description': _('Abstract is too short. Try a larger text.')})
                elif detect(description_text) != 'en':
                    error.update({'description': _('Abstract is not in English.')})
            except:
                error.update({'description': _('Abstract is invalid')})
        
        description_es =  post.get('description_es', '')
        if not description_es:
            error.update({'description_es': _('Abstract is required')})
        else:
            try:
                description_es_text = html2plaintext(description_es)
                description_es_text = description_es_text.replace('  ', ' ') 
                if len(description_es_text.split(' ')) < 50:
                    error.update({'description_es': _('Abstract is too short. Try a larger text.')})
                elif detect(description_es_text) != 'es':
                    error.update({'description_es': _('Abstract is not in Spanish.')})
            except:
                error.update({'description_es': _('Abstract is invalid')})

        
        tags = []
        keywords = post.get('keywords', "")        
        keywords_list = keywords.split(',')
        
        for kw in keywords_list:
            kw = kw.strip()
            kw = kw.rstrip()
            kw = kw.lower()
            if kw:
                event_tag = request.env['event.track.tag'].sudo().search([('name', '=', kw)])
                if not event_tag:
                    event_tag = request.env['event.track.tag'].sudo().create({'name': kw})
                
                tags.append(event_tag.id)
        
        if not len(tags):
            error.update({'keywords': _('Add some keywords')})
        
        tags_es = []
        keywords_es = post.get('keywords_es', "")
        keywords_es_list = keywords_es.split(',')
        
        for kw in keywords_es_list:
            kw = kw.strip()
            kw = kw.rstrip()
            kw = kw.lower()
            if kw:
                event_tag = request.env['event.track.tag'].sudo().search([('name', '=', kw)])
                if not event_tag:
                    event_tag = request.env['event.track.tag'].sudo().create({'name': kw})
                
                tags_es.append(event_tag.id)
        if not len(tags_es):
            error.update({'keywords_es': _('Add some keywords')})

        tags_all = tags + tags_es

        authors = []
        authors_data = post.get('authors', "")
        try:
            authors_list_data = json.loads(authors_data)
        except:
            error.update({'authors': _('Authors are not in a valid format')})
            return request.render("website_event_track.event_track_proposal", {'error': error, 'post': post, 'event': event, 'countries': countries, 'main_object': event})
        
        author_errors = False
        emails = [request.env.user.partner_id.email]
        for au in authors_list_data:
            if au.get('author_id') == 0:
                authors.append(request.env.user.partner_id.id)
            else:
                au_name = au.get('author_name', '')
                if not au_name:
                    au.update({'error':{'author_name':_('Name is required')}})
                    author_errors = True
                
                au_email = au.get('author_email', '')
                if not au_email:
                    au.update({'error':{'author_email':_('Email is required')}})
                    author_errors = True
                else:
                    if au_email in emails:
                        au.update({'error':{'author_email':_('Different authors can not use the same email address')}})
                        author_errors = True
                    else:
                        emails.append(au_email)
                
                au_institution = au.get('author_institution', '')
                au_country_id = au.get('author_country_id', 0)
                if not au_country_id:
                    au.update({'error':{'author_country_id':_('Country is required')}})
                    author_errors = True
                else:
                    try:
                        au_country_id = int(au_country_id)
                        country = request.env['res.country'].sudo().search([('id', '=', au_country_id)])
                    except ValueError:
                        pass
                    
                    if not country:
                        au.update({'error':{'author_country_id':_('Country is invalid')}})
                        author_errors = True
                    else:
                        author = request.env['res.partner'].sudo().search([('email', '=', au_email), ('name', '=', au_name), ('country_id', '=', au_country_id)], limit=1)
                        if not author:
                            author = request.env['res.partner'].sudo().create({'name': au_name, 'email': au_email, 'institution': au_institution, 'country_id': au_country_id})
                        
                        authors.append(author.id)
        
        if author_errors:
            error.update({'authors': _('Authors have some errors')})
            post.update({'authors': json.dumps(authors_list_data)})
        
        if error:
            return request.render("website_event_track.event_track_proposal", {'error': error, 'post': post, 'event': event,'countries': countries, 'main_object': event})

        track = request.env['event.track'].sudo().create({
            'name': track_name,
            'partner_name': request.env.user.partner_id.name, 
            'partner_email': request.env.user.partner_id.email, 
            'partner_phone': request.env.user.partner_id.phone, 
            'partner_biography': request.env.user.partner_id.website_description,
            'event_id': event.id,
            'tag_ids': [(6, 0, tags_all)],
            'language_id': language_id,
            'user_id': event.user_id.id, 
            'publish_complete': post.get('publish_complete', False),
            'partner_id': request.env.user.partner_id.id,
            'description': description,
            'description_es': description_es,
        })        

        i = 1
        for au_id in authors:
            request.env['event.track.author'].sudo().create({
                'track_id': track.id,
                'partner_id': au_id,
                'sequence': i,
            })
            i += 1

        translation = request.env['ir.translation'].sudo().search([('name', '=', 'event.track,name'),
            ('lang', '=', 'es_ES'), ('res_id', '=', track.id), ('type', '=', 'model')])
        if translation:
            translation.write({'value': track_name_es, 'state': 'translated'})
        else:
            request.env['ir.translation'].sudo().create(
                {
                    'name': 'event.track,name',
                    'lang': 'es_ES',
                    'type': 'model',
                    'res_id': track.id,
                    'src': track_name,
                    'value': track_name_es, 
                    'state': 'translated'
                })        

        if request.env.user != request.website.user_id:
            track.sudo().message_subscribe(partner_ids=request.env.user.partner_id.ids)
        else:
            partner = request.env['res.partner'].sudo().search([('email', '=', post['email_from'])])
            if partner:
                track.sudo().message_subscribe(partner_ids=partner.ids)

        for c_file in request.httprequest.files.getlist('file'):
            data = c_file.read()
            if data and c_file.filename:
                request.env['ir.attachment'].sudo().create({
                            'name': c_file.filename,
                            'raw': data,
                            'public': False,
                            'res_model': 'event.track',
                            'res_id': track.id
                        })
                    
        # add the reviewers automatically
        for reviewer in event.sudo().reviewer_ids:
            request.env['event.track.review'].sudo().create({
                'track_id': track.id,
                'partner_id': reviewer.partner_id.id,
                'weight': reviewer.weight,
                'state': 'notice',
            })
        review_stage = request.env.ref('website_event_track.event_track_stage1', raise_if_not_found=False)
        if len(event.reviewer_ids)>1 and review_stage:
            track.write({'stage_id': review_stage.id})

        

        return request.render("website_event_track.event_track_proposal", {'track': track, 'event': event,'countries': countries, 'main_object':event, 'error': error})