# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions, SUPERUSER_ID, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    event_track_count = fields.Integer("Event Tracks", compute='_compute_event_track_count', help="Number of tracks.", store=True)
    event_track_done_count = fields.Integer("Event Tracks Done", compute='_compute_event_track_count', help="Number of done tracks.", store=True)
    event_track_ids = fields.One2many("event.track", "partner_id", string="Tracks")
    event_track_author_count = fields.Integer("Event Tracks Author", compute='_compute_event_track_author_count', help="Number of tracks as author.", store=True)
    event_track_author_ids = fields.One2many('event.track.author', 'partner_id', string='Author Tracks')
    
    @api.depends('event_track_ids',)
    def _compute_event_track_count(self):
        for partner in self:
            partner.event_track_count = len(partner.event_track_ids)
            partner.event_track_done_count = len(partner.event_track_ids.filtered(lambda r: r.stage_id.is_done))
    
    
    @api.depends('event_track_author_ids',)
    def _compute_event_track_author_count(self):
        for partner in self:
            partner.event_track_author_count = len(partner.event_track_author_ids)

    
    def action_event_track_view(self):
        action = self.env.ref('website_event_track.action_event_track').read()[0]
        action['context'] = {}
        action['domain'] = [('partner_id', 'child_of', self.ids)]
        return action

    
    def action_event_track_author_view(self):
        action = self.env.ref('website_event_track.action_event_track').read()[0]
        action['context'] = {}
        action['domain'] = [('author_ids.partner_id', 'child_of', self.ids)]
        return action
    
    def unlink(self):
        if self.create_uid.id == self.env.user.id or self.env.user.id == SUPERUSER_ID:
            return super(ResPartner, self).unlink()
        else:
            raise exceptions.Warning(_("You can not delete this partner because it was created by other user"))

    def split(self):
        """splits into single partners"""
        
        name = str(self.name)
        partners = name.split(',')
        created = []
        if len(partners)>1:
            for p in partners:
                p = p.strip()
                p = p.rstrip()
                if p:
                    partner = self.env['res.partner'].create({'name': p})
                    created.append(partner)
        
        for c in created:
            for track in self.event_track_author_ids:
                c.track_ids = [(4, track.id)]
        
        
        

    
