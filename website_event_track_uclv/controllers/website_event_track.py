# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
import pytz
import json

from odoo import fields, http
from collections import OrderedDict
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, plaintext2html
from odoo.addons.website_event_track.controllers.event_track import EventTrackController
from werkzeug.exceptions import NotFound, Forbidden
from langdetect import detect


class UCLVWebsiteEventTrackController(EventTrackController):

    """@http.route(['''/event/<model("event.event"):event>/track/<model("event.track", "[('event_id','=',event[0])]"):track>'''], type='http', auth="public", website=True)
    def event_track_view(self, event, track, **post):
        track = track.sudo()
        values = {'track': track, 'event': track.event_id, 'main_object': track}
        return request.render("website_event_track.track_view", values)"""

    """def _get_locale_time(self, dt_time, lang_code):
        locale = babel.Locale.parse(lang_code)
        return babel.dates.format_time(dt_time, format='short', locale=locale)"""

    """def _prepare_calendar(self, event, event_track_ids):
        local_tz = pytz.timezone(event.date_tz or 'UTC')
        lang_code = request.env.context.get('lang')
        locations = {}                  # { location: [track, start_date, end_date, rowspan]}
        dates = []                      # [ (date, {}) ]
        for track in event_track_ids:
            locations.setdefault(track.location_id or False, [])

        forcetr = True
        for track in event_track_ids:
            start_date = fields.Datetime.from_string(track.date).replace(tzinfo=pytz.utc).astimezone(local_tz)
            end_date = start_date + datetime.timedelta(hours=(track.duration or 0.5))
            location = track.location_id or False
            locations.setdefault(location, [])

            # New TR, align all events
            if forcetr or (start_date>dates[-1][0]) or not location:
                formatted_time = self._get_locale_time(start_date, lang_code)
                dates.append((start_date, {}, bool(location), formatted_time))
                for loc in list(locations):
                    if locations[loc] and (locations[loc][-1][2] > start_date):
                        locations[loc][-1][3] += 1
                    elif not locations[loc] or locations[loc][-1][2] <= start_date:
                        locations[loc].append([False, locations[loc] and locations[loc][-1][2] or dates[0][0], start_date, 1])
                        dates[-1][1][loc] = locations[loc][-1]
                forcetr = not bool(location)

            # Add event
            if locations[location] and locations[location][-1][1] > start_date:
                locations[location][-1][3] -= 1
            locations[location].append([track, start_date, end_date, 1])
            dates[-1][1][location] = locations[location][-1]
        return {
            'locations': locations,
            'dates': dates
        }"""

    """@http.route(['''/event/<model("event.event"):event>/agenda'''], type='http', auth="public", website=True, sitemap=False)
    def event_agenda(self, event, tag=None, **post):
        days_tracks = collections.defaultdict(lambda: [])
        for track in event.track_ids.sorted(lambda track: (track.date or '', bool(track.location_id))):
            if not track.date:
                continue
            days_tracks[track.date[:10]].append(track)

        days = {}
        tracks_by_days = {}
        for day, tracks in days_tracks.items():
            tracks_by_days[day] = tracks
            days[day] = self._prepare_calendar(event, tracks)

        return request.render("website_event_track.agenda", {
            'event': event,
            'main_object': event,
            'days': days,
            'tracks_by_days': tracks_by_days,
            'tag': tag
        })"""

    """@http.route(['''/event/<model("event.event"):event>/intro'''], type='http', auth="public", website=True, sitemap=False)
    def event_intro(self, event, tag=None, **post):
        event = event.with_context(pricelist=request.website.get_current_pricelist().id)
        return request.render("website_event_uclv.template_intro", {
            'event': event,
            'main_object': event
        })"""
    
    """@http.route(['''/event/<model("event.event"):event>/location'''], type='http', auth="public", website=True, sitemap=False)
    def event_location(self, event, tag=None, **post):
        return request.render("website_event_uclv.template_intro", {
            'event': event,
            'main_object': event
        })"""   


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
                        author = request.env['res.partner'].sudo().search([('email', '=', au_email), ('name', '=', au_name), ('country_id', '=', au_country_id)])
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
        return request.render("website_event_track.event_track_proposal", {'track': track, 'event': event,'countries': countries, 'main_object':event, 'error': error})