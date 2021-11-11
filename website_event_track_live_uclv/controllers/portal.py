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
from werkzeug.exceptions import NotFound, Forbidden, InternalServerError, BadGateway
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


class PortalController(TrackPortalController):    
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
                
        
        import requests
        from requests_toolbelt.multipart import encoder

        Params = request.env['ir.config_parameter'].sudo()
        avideo_base_domain = Params.get_param('avideo.base.domain','')
        if avideo_base_domain[:-1] != '/':
            avideo_base_domain +='/'
            
        url = avideo_base_domain + 'plugin/MobileManager/upload.php?user='
        avideo_user = Params.get_param('avideo.user','')
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
            if response:
                try:
                    import json
                    response = json.loads(response.text)
                    print(response)
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
            
                except:
                    print('Response from encoder not in json')                    
                    raise InternalServerError()

            else:
                print('no response from encoder')
                raise BadGateway() 
              
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

    
