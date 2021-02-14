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