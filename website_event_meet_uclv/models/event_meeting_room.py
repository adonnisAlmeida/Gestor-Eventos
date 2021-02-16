# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug


class EventMeetingRoom(models.Model):
    _inherit = "event.meeting.room"
    
    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if not values.get("chat_room_id") and not values.get('room_name'):
                event_name = 'uclv'
                if values.get('event_id', False):
                    event_name = self.env['event.event'].browse(values.get('event_id')).name
                values['room_name'] = '%s-room-%s' % (event_name, values['name'])
        return super(EventMeetingRoom, self).create(values_list)