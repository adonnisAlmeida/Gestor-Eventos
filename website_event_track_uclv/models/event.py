# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID, _
from odoo.addons.http_routing.models.ir_http import slug
import datetime


class EventType(models.Model):
    _inherit = 'event.type'

    website_registration = fields.Boolean('Registration on Website')

    
class Event(models.Model):
    _inherit = 'event.event'
        
    number = fields.Char(string='Sequence')
    email = fields.Char('Email')

    strict_review_workflow = fields.Boolean(default=True)
    track_ids = fields.One2many('event.track', 'event_id', 'Tracks')
    track_count = fields.Integer('Tracks', compute='_compute_track_count')

    sponsor_ids = fields.One2many('event.sponsor', 'event_id', 'Sponsors')
    sponsor_count = fields.Integer('Sponsors', compute='_compute_sponsor_count')

    website_registration = fields.Boolean('Registration on Website', compute='_compute_website_registration', inverse='_set_website_menu')
    website_registration_ok = fields.Boolean('Registration on Website')
           
    def _get_overdue(self):
        overdue = False
        if self.paper_abstract_deadline:
            if self.paper_abstract_deadline < fields.Date.today():
                overdue = True
        self.paper_abstract_deadline_overdue = overdue
    
    def _get_month(self):
        months = {1: _('jan'), 2: _('feb'), 3: _('mar'), 4: _('apr'),
                  5: _('may'), 6: _('jun'), 7: _('jul'), 8: _('agu'),
                  9: _('sep'), 10: _('oct'), 11: _('nov'), 12: _('dec')}
        month = '01'
        if self.paper_abstract_deadline:
            month = months[self.paper_abstract_deadline.month]
        
        self.paper_abstract_deadline_month = month
    
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'event.event')], string='Attachments')
    paper_abstract_deadline = fields.Date(string="Abstracts Deadline")
    paper_abstract_deadline_month = fields.Char(string="Abstracts Deadline Month", compute='_get_month')
    paper_abstract_deadline_overdue = fields.Boolean(string="Abstracts Deadline Overdue", compute='_get_overdue')

    paper_abstract_notification_date = fields.Date(string="Abstracts Acceptance Notification Date")
    paper_final_deadline = fields.Date(string="Final Papers Deadline")

    def get_current_user(self):
        self.current_user = self.env.user.id
    
    current_user = fields.Many2one('res.users', compute='get_current_user')
    allowed_language_ids = fields.Many2many('res.lang', relation='event_allowed_language_rel', string='Available Track Languages')
    allowed_country_ids = fields.One2many('res.country', compute='get_countries')    
    
    def _compute_website_registration(self):
        for event in self:
            event.website_registration = event.website_registration_ok
    
    def _get_track_menu_entries(self):
        """ Method returning menu entries to display on the website view of the
        event, possibly depending on some options in inheriting modules.

        Each menu entry is a tuple containing :
          * name: menu item name
          * url: if set, url to a route (do not use xml_id in that case);
          * xml_id: template linked to the page (do not use url in that case);
          * menu_type: key linked to the menu, used to categorize the created
            website.event.menu;
        """
        self.ensure_one()
        return [
            ('Papers', '/event/%s/track' % slug(self), False, 10, 'track'),
            ('Agenda', '/event/%s/agenda' % slug(self), False, 70, 'track')
        ]

    def _get_track_proposal_menu_entries(self):
        """ See website_event_track._get_track_menu_entries() """
        self.ensure_one()
        return [('Submit a paper', '/event/%s/track_proposal' % slug(self), False, 15, 'track_proposal')]

    @api.model
    def create(self, vals):
        padl = vals.get('paper_abstract_deadline', False)
        pand = vals.get('paper_abstract_notification_date', False)
        pfdl = vals.get('paper_final_deadline', False)
        date_begin = vals.get('date_begin')
        
        if not self.env.context.get('ignore_errors', False):
            if padl and padl > date_begin:
                raise exceptions.Warning(_("The deadline to accept abstracts can not be older than event begin date."))
            if pand and pand > date_begin:
                raise exceptions.Warning(_("Notification date can not be older than event begin date"))
            if pfdl and pfdl > date_begin:
                raise exceptions.Warning(_("The deadline tu submit final papers can not be older than event begin date"))
            if pand and not padl:
                raise exceptions.Warning(_("Events without a deadline to accept abstracts can not have a notification date"))
            if pand and padl:
                if pand < padl:
                    raise exceptions.Warning(_("Notification date can not be earlier than the deadline to accept abstracts"))
            if padl and pfdl:
                if pfdl < padl:
                    raise exceptions.Warning(_("The deadline tu submit final papers can not be earlier than the deadline to accept abstracts"))
            
        
        return super(Event, self).create(vals)
    
    def write(self, vals):
        group = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group.sudo().users:
            if  self.user_id.id != self.env.user.id:
                raise exceptions.Warning("You are not authorized to change this event")
        
        padl = vals.get('paper_abstract_deadline', self.paper_abstract_deadline and self.paper_abstract_deadline.strftime('%Y-%m-%d'))
        pand = vals.get('paper_abstract_notification_date', self.paper_abstract_notification_date and self.paper_abstract_notification_date.strftime('%Y-%m-%d'))
        pfdl = vals.get('paper_final_deadline', self.paper_final_deadline and self.paper_final_deadline.strftime('%Y-%m-%d'))
        date_begin = vals.get('date_begin', self.date_begin.strftime('%Y-%m-%d'))
        
        if not self.env.context.get('ignore_errors', False):
            if padl and padl > date_begin:
                raise exceptions.Warning(_("The deadline to accept abstracts can not be older than event begin date"))
            if pand and pand > date_begin:
                raise exceptions.Warning(_("Notification date can not be older than event begin date"))
            if pfdl and pfdl > date_begin:
                raise exceptions.Warning(_("The deadline tu submit final papers can not be older than event begin date"))
            if pand and not padl:
                raise exceptions.Warning(_("Events without a deadline to accept abstracts can not have a notification date"))
            if pand and padl:
                if pand < padl:
                    raise exceptions.Warning(_("Notification date can not be earlier than the deadline to accept abstracts"))
            if padl and pfdl:
                if pfdl < padl:
                    raise exceptions.Warning(_("The deadline tu submit final papers can not be earlier than the deadline to accept abstracts"))
        return super(Event, self).write(vals)
