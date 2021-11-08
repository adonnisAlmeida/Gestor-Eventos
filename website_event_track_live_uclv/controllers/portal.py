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
from odoo.addons.website_event_track_uclv.controllers.portal import PortalController as TrackPortalController
from werkzeug.exceptions import NotFound, Forbidden, InternalServerError
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from langdetect import detect


class PortalController(TrackPortalController):    
    @http.route(['''/my/paper/<int:track_id>'''], type='http', auth="public", website=True)
    def portal_my_paper(self, track_id, access_token=None, report_type=None, download=False, **post):
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

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=prop, report_type=report_type, report_ref='website_event_track_uclv.report_event_track', download=download)
        
        countries = request.env['res.country'].sudo().search([])
        error = {}
        warning = {}
        success = {}
        info = {}
        if not prop.is_done and prop.stage_id.can_edit and not prop.event_id.paper_final_deadline_overdue and prop.event_id.paper_final_deadline:
            info.update({'global': _('You can edit this paper until %s') % prop.event_id.paper_final_deadline})

        if post:            
            if not prop.is_done:
                for c_file in request.httprequest.files.getlist('file'):
                    data = c_file.read()
                    import base64
                    if data:
                        request.env['ir.attachment'].sudo().create({
                                    'name': c_file.filename,
                                    'datas': base64.b64encode(data),
                                    'public': False,
                                    'res_model': 'event.track',
                                    'res_id': prop.id,                                    
                                })
            else:
                error = error.update({'global': _('You can not edit this paper because it is done')})
                return request.render("website_event_track_uclv.portal_my_paper", {'error': error, 'paper': prop, 'info': info, 'warning': warning})
            
            can_edit = prop.stage_id.can_edit and not prop.event_id.paper_final_deadline_overdue
            if not can_edit:
                error = error.update({'global': _('You can not edit this paper because it is done')})
                return request.render("website_event_track_uclv.portal_my_paper", {'error': error, 'paper': prop, 'info': info, 'warning': warning})

            language_id = post.get('language_id', False)        
            if not language_id:
                error.update({'language_id': _('Language is required')})
            else:
                try:
                    language_id = int(language_id)
                    if language_id not in prop.event_id.allowed_language_ids.mapped('id'):
                        error.update({'language_id': _('Language not allowed')})
                except ValueError:
                    error.update({'language_id': _('Language not allowed')})
            
            authors = []
            authors_data = post.get('authors', "")
            try:
                authors_list_data = json.loads(authors_data)
            except:
                error.update({'authors': _('Authors are not in a valid format')})
                return request.render("website_event_track_uclv.portal_my_paper", {'error': error, 'post': post, 'paper': prop, 'authors': prop.authors_json(), 'countries': countries, 'info': info, 'warning': warning})
            
            author_errors = False
            emails = []
            for au in authors_list_data:
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
                        # everything ok let's create or update the author
                        if can_edit:
                            author = request.env['res.partner'].sudo().search([('email', '=', au_email), ('name', '=', au_name), ('country_id', '=', au_country_id)])
                            if not author:
                                author = request.env['res.partner'].sudo().create({'name': au_name, 'email': au_email, 'institution': au_institution, 'country_id': au_country_id})
                            
                            authors.append(author.id)
            
            if author_errors:
                error.update({'authors': _('Authors have some errors')})
                post.update({'authors': json.dumps(authors_list_data)})
            
            if error:
                return request.render("website_event_track_uclv.portal_my_paper", {'error': error, 'post': post, 'paper': prop, 'authors': prop.authors_json(), 'countries': countries, 'info': info, 'warning': warning})
            
            # delete unused authors
            old = []
            for x in prop.author_ids:
                old.append(x.partner_id.id)
            
            authors.append(prop.partner_id.id)
            to_delete = list(set(old) - set(authors))

            to_delete = request.env['event.track.author'].sudo().search([('track_id', '=', prop.id), ('partner_id', 'in', to_delete)])
            for item in to_delete:                
                item.sudo().unlink()

            #update and create
            i = 1
            for au_id in authors:
                exists = request.env['event.track.author'].sudo().search([('track_id', '=', prop.id), ('partner_id', '=', au_id)])
                if exists:
                    exists.sudo().write({'sequence': i})
                else:
                    request.env['event.track.author'].sudo().create({
                        'track_id': prop.id,
                        'partner_id': au_id,
                        'sequence': i,
                    })
                
                i += 1

            #name =  post.get('name', prop.with_context(lang='en_US').name)
            name =  post.get('name', '')        
            if not name:
                error.update({'name': _('Title is required')})
            else:
                name = name.strip().rstrip()
                if not name:
                    error.update({'name': _('Title is invalid')})

            #name_es =  post.get('name_es', prop.with_context(lang='es_ES').name)
            name_es =  post.get('name_es', '')
            if not name_es:
                error.update({'name_es': _('Title is required')})
            else:
                name_es = name_es.strip().rstrip()
                if not name_es:
                    error.update({'name_es': _('Title is invalid')})

            #description =  post.get('description', prop.description)
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

            #description_es =  post.get('description_es', prop.description_es)
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

            #introduction =  post.get('introduction', prop.introduction)
            introduction =  post.get('introduction', '')
            if not introduction:
                warning.update({'introduction': _('This field must be filled in order to publish this paper')})
            else:
                try:
                    introduction_text = html2plaintext(introduction)
                    introduction_text = introduction_text.replace('  ', ' ') 
                    if len(introduction_text.split(' ')) < 50:
                        warning.update({'introduction': _('This field is too short. Try a larger text.')})
                    else:
                        if language_id in prop.event_id.allowed_language_ids.mapped('id'):
                            lang = request.env["res.lang"].browse(language_id)
                            if lang:
                                if detect(introduction_text) != lang.iso_code[0:2]:
                                    warning.update({'introduction': _('This field must be written in Main Language: %s') %lang.name})
                except:
                    error.update({'introduction': _('This field is invalid')})

            #methodology =  post.get('methodology', prop.methodology)
            methodology =  post.get('methodology', '')
            if not methodology:
                warning.update({'methodology': _('This field must be filled in order to publish this paper')})
            else:
                try:
                    methodology_text = html2plaintext(methodology)
                    methodology_text = methodology_text.replace('  ', ' ') 
                    if len(methodology_text.split(' ')) < 50:
                        warning.update({'methodology': _('This field is too short. Try a larger text.')})
                    else:
                        if language_id in prop.event_id.allowed_language_ids.mapped('id'):
                            lang = request.env["res.lang"].browse(language_id)
                            if lang:
                                if detect(methodology_text) != lang.iso_code[0:2]:
                                    warning.update({'methodology': _('This field must be written in Main Language: %s') %lang.name})
                except:
                    error.update({'methodology': _('This field is invalid')})
            
            #results =  post.get('results', prop.results)
            results =  post.get('results', '')
            if not results:
                warning.update({'results': _('This field must be filled in order to publish this paper')})
            else:
                try:
                    results_text = html2plaintext(results)
                    results_text = methodology_text.replace('  ', ' ') 
                    if len(results_text.split(' ')) < 50:
                        warning.update({'results': _('This field is too short. Try a larger text.')})
                    else:
                        if language_id in prop.event_id.allowed_language_ids.mapped('id'):
                            lang = request.env["res.lang"].browse(language_id)
                            if lang:
                                if detect(results_text) != lang.iso_code[0:2]:
                                    warning.update({'results': _('This field must be written in Main Language: %s') %lang.name})
                except:
                    error.update({'results': _('This field is invalid')})
            
            #conclussions =  post.get('conclussions', prop.conclussions)
            conclussions =  post.get('conclussions', '')
            if not conclussions:
                warning.update({'conclussions': _('This field must be filled in order to publish this paper')})
            else:
                try:
                    conclussions_text = html2plaintext(conclussions)
                    conclussions_text = conclussions_text.replace('  ', ' ') 
                    if len(conclussions_text.split(' ')) < 50:
                        warning.update({'conclussions': _('This field is too short. Try a larger text.')})
                    else:
                        if language_id in prop.event_id.allowed_language_ids.mapped('id'):
                            lang = request.env["res.lang"].browse(language_id)
                            if lang:
                                if detect(conclussions_text) != lang.iso_code[0:2]:
                                    warning.update({'conclussions': _('This field must be written in Main Language: %s') %lang.name})
                except:
                    error.update({'conclussions': _('This field is invalid')})
            
            #bibliographic =  post.get('bibliographic', prop.bibliographic)        
            bibliographic =  post.get('bibliographic', '')
            if not bibliographic:
                warning.update({'bibliographic': _('This field must be filled in order to publish this paper')})
            else:
                try:
                    bibliographic_text = html2plaintext(bibliographic)
                    bibliographic_text = conclussions_text.replace('  ', ' ') 
                    if len(bibliographic_text.split(' ')) < 50:
                        warning.update({'bibliographic': _('This field is too short. Try a larger text.')})
                except:
                    error.update({'bibliographic': _('This field is invalid')})

            if error:
                return request.render(
                "website_event_track_uclv.portal_my_paper", {
                    'paper': prop,
                    'authors': prop.authors_json(),
                    'countries':countries,
                    'post': post,
                    'error': error,
                    'info': info,
                    'warning': warning,
                })

            
            prop.sudo().with_context(lang='en_US').write({
                'name': name,
                'description': description
            })
            prop.sudo().write({
                'tag_ids': [(6, 0, tags)],
                'language_id': language_id,
                'description_es': description_es,
                'introduction': introduction,
                'methodology': methodology, 
                'results': results,                
                'conclussions': conclussions,
                'bibliographic': bibliographic,
                })

            translation = request.env['ir.translation'].sudo().search([('name', '=', 'event.track,name'),
                ('lang', '=', 'es_ES'), ('res_id', '=', prop.id), ('type', '=', 'model')])
            if translation:
                translation.write({'src': name, 'value': name_es, 'state': 'translated'})
            else:
                request.env['ir.translation'].sudo().create(
                    {
                        'name': 'event.track,name',
                        'lang': 'es_ES',
                        'type': 'model',
                        'res_id': prop.id,
                        'src': name,
                        'value': name_es, 
                        'state': 'translated'
                    })
            
            request.cr.commit()
            
            success.update({'global': _('Changes successfully saved')})        
        
        return request.render(
            "website_event_track_uclv.portal_my_paper", {
                'paper': prop,
                'authors': prop.authors_json(),
                'countries':countries,
                'error': error,
                'warning': warning,
                'info': info,
                'success': success
            })




       
        import requests
        from requests_toolbelt.multipart import encoder

        Params = request.env['ir.config_parameter'].sudo()
        avideo_base_domain = Params.get_param('avideo.base.domain','https://video-convencion.uclv.cu/')
        url = avideo_base_domain + 'plugin/MobileManager/upload.php?user='
        avideo_user = Params.get_param('avideo.user','admin')
        url += avideo_user
        avideo_password = Params.get_param('avideo.password','')
        url += '&pass=' + avideo_password

        session = requests.Session()
        for c_file in request.httprequest.files.getlist('video'):
            form = encoder.MultipartEncoder({
                "upl": (c_file.filename, c_file, "application/octet-stream"),
                'description': prop.description[:256], 
                'title': prop.with_context(lang="en_US").name[:128]
            })
            headers = {"Prefer": "respond-async", "Content-Type": form.content_type}
            response = session.post(url, headers=headers, data=form)
            
            import json
            response = json.loads(response.text)
            if not response['error']:
                # delete old video
                if prop.avideo_url:
                    try:
                        old_video_id = prop.avideo_url.split('/')[0]
                        url = avideo_base_domain + 'objects/videoDelete.json.php?user='
                        url += avideo_user
                        url += '&pass=' + avideo_password
                        session.post(url, headers=False, data={'id': old_video_id})
                    except:
                        pass
                
                prop.write({'avideo_url': str(response['videos_id'])+'/'+prop.with_context(lang="en_US").name[:128]})
            
        session.close()

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

    
