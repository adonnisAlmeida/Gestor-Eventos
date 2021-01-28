# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
import pytz

from odoo import fields, http
from collections import OrderedDict
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, plaintext2html
from odoo.addons.website_event_track.controllers.event_track import EventTrackController
from werkzeug.exceptions import NotFound, Forbidden


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

    """@http.route([
        '''/event/<model("event.event"):event>/track'''        
        ], type='http', auth="public", website=True, sitemap=False)
    def event_tracks(self, event, **searches):
        
        searches.setdefault('tag', 'all')
        searches.setdefault('lang', 'all')
        searches.setdefault('type', 'all')
        
        tracks = request.env['event.track'].sudo().search(['|','|','|','|',("user_id", "=", request.env.user.id),('partner_id', '=', request.env.user.partner_id.id),('reviewer_id', '=', request.env.user.id),('reviewer2_id', '=', request.env.user.id),('website_published','=', True),('event_id', '=', event.id)])
        
        tags = []
        languages = []
        types = []
        for track in tracks:
            if track.language_id:
                found = False
                for l in languages:
                    if l == track.language_id:
                        found = True
                        break
                if not found:
                    languages.append(track.language_id)
            
            if track.track_type_id:
                found = False
                for t in types:
                    if t == track.track_type_id:
                        found = True
                        break
                if not found:
                    types.append(track.track_type_id)

            for t in track.tag_ids:
                found = False
                for i in range(0, len(tags)):
                    if tags[i]['tag'] == t:
                        found = True
                        tags[i]['times'] += 1
                if not found:
                    tags.append({'tag': t, 'times': 1})

        if searches['tag']!='all':
            tracks = tracks.filtered(lambda track: int(searches['tag']) in [t.id for t in track.tag_ids])
        if searches['lang']!='all':
            tracks = tracks.filtered(lambda track: str(track.language_id.id) == searches['lang'])
        if searches['type']!='all':
            tracks = tracks.filtered(lambda track: str(track.track_type_id.id) == searches['type'])
        
        
        
        tags = sorted(tags, key=lambda item: item['times'], reverse=True)[0:30]
        ordered_tags = [item['tag'] for item in tags]

        
        values = {
            'event': event,
            'main_object': event,
            'tracks': tracks,
            'tags': ordered_tags,
            'languages': languages,
            'types': types,
            'searches': searches,
            'html2plaintext': html2plaintext
        }
        return request.render("website_event_track.tracks", values)
"""
    @http.route(['''/event/<model("event.event"):event>/track_proposal'''], type='http', auth="user", website=True, sitemap=False)
    def event_track_proposal(self, event, **post):
        if not event.can_access_from_current_website():
            raise NotFound()

        return request.render("website_event_track.event_track_proposal", {'event': event, 'main_object': event})

    @http.route(['/event/<model("event.event"):event>/track_proposal/post'], type='http', auth="user", methods=['POST'], website=True)
    def event_track_proposal_post(self, event, **post):
        if not event.can_access_from_current_website():
            raise NotFound()

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

        authors = [request.env.user.partner_id.id]
        other_authors = post.get('other_authors', "")
        other_authors_list = other_authors.split(',')
        
        for oa in other_authors_list:
            oa = oa.strip()
            oa = oa.rstrip()
            oa = oa.capitalize()
            if oa:
                author = request.env['res.partner'].sudo().search([('name', '=', oa)])
                if not author:
                    author = request.env['res.partner'].sudo().create({'name': oa})
                
                authors.append(author.id)

        track = request.env['event.track'].sudo().create({
            'name': post['track_name'],
            'partner_name': request.env.user.partner_id.name, #'partner_name': post['partner_name'],
            'partner_email': request.env.user.partner_id.email, #'partner_email': post['email_from'],
            'partner_phone': request.env.user.partner_id.phone, #'partner_phone': post['phone'],
            'partner_biography': request.env.user.partner_id.website_description, #'partner_biography': plaintext2html(post['biography']),
            'event_id': event.id,
            'tag_ids': [(6, 0, tags)],
            'author_ids': [(6, 0, authors)],
            'language_id': post.get('language_id', False),
            'user_id': event.user_id.id, #'user_id': False,
            'publish_complete': post.get('publish_complete', False),
            'partner_id': request.env.user.partner_id.id,
            'description': post['description'],
            #'image': base64.b64encode(post['image'].read()) if post.get('image') else False
        })
        translation = request.env['ir.translation'].sudo().search([('name', '=', 'event.track,name'),
            ('lang', '=', 'es_ES'), ('res_id', '=', track.id), ('type', '=', 'model')])
        if translation:
            translation.write({'value': post['track_name_es'], 'state': 'translated'})

        translation2 = request.env['ir.translation'].sudo().search([('name', '=', 'event.track,description'),
            ('lang', '=', 'es_ES'), ('res_id', '=', track.id), ('type', '=', 'model_terms')])
        if translation2:
            translation2.write({'value': post['description_es'], 'state': 'translated'})
        else:
            translation2 =  request.env['ir.translation'].sudo().create(
                {
                    'name': 'event.track,description',
                    'lang': 'es_ES',
                    'type': 'model_terms',
                    'res_id': track.id,
                    'src': html2plaintext(post['description']),
                    'value': html2plaintext(post['description_es']), 
                    'state': 'translated'
                }
            )

             

        for c_file in request.httprequest.files.getlist('file'):
            data = c_file.read()
            import base64
            request.env['ir.attachment'].sudo().create({
                        'name': c_file.filename,
                        'datas': base64.b64encode(data),
                        
                        'public': False,
                        'res_model': 'event.track',
                        'res_id': track.id
                    })
       
        if request.env.user != request.website.user_id:
            track.sudo().message_subscribe(partner_ids=request.env.user.partner_id.ids)
        else:
            partner = request.env['res.partner'].sudo().search([('email', '=', post['email_from'])])
            if partner:
                track.sudo().message_subscribe(partner_ids=partner.ids)
        return request.render("website_event_track.event_track_proposal_success", {'track': track, 'event': event})