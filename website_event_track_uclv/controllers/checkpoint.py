# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel
import collections
import datetime
import pytz

from odoo import fields, http
from collections import OrderedDict
from odoo.tools.translate import _
from odoo.tools import html_escape as escape, html2plaintext, consteq
from odoo.http import Controller, request, route
from werkzeug.exceptions import NotFound, Forbidden
from odoo.exceptions import AccessError


class CheckpointController(Controller):
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
    
    @http.route(['''/events/auth/<token>'''], type='http', auth="public", website=True)
    def event_authenticity(self, token, **kw):
        reg = request.env['event.registration'].sudo().search([('authenticity_token', '=', token)])
        track = request.env['event.track'].sudo().search([('authenticity_token', '=', token)])
        
        return request.render(
                "website_event_track_uclv.event_authenticity", {
                    'registration': reg,
                    'track': track
                })

