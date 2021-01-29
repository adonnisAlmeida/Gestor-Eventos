# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID, _
from odoo.addons.http_routing.models.ir_http import slug
import datetime
from odoo.modules import get_module_resource
import base64


class EventType(models.Model):
    _inherit = 'event.type'

    website_registration = fields.Boolean('Registration on Website')
    
    """@api.onchange('website_menu')
    def _onchange_website_menu(self):
        if not self.website_menu:
            self.website_registration = False
            self.website_track = False
            self.website_track_proposal = False """


class Event(models.Model):
    _inherit = 'event.event'
        
    number = fields.Char(string='Sequence')
    email = fields.Char('Email')

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
        return [('Upload a paper', '/event/%s/track_proposal' % slug(self), False, 15, 'track_proposal')]

    """@api.onchange('event_type_id')
    def _onchange_type(self):
        super(Event, self)._onchange_type()
        if self.event_type_id and self.website_menu:
            self.website_registration = self.event_type_id.website_registration
            self.website_track = self.event_type_id.website_track
            self.website_track_proposal = self.event_type_id.website_track_proposal
    """
    
    """@api.onchange('website_menu')
    def _onchange_website_menu(self):
        if not self.website_menu:
            self.website_registration = False
            self.website_track = False
            self.website_track_proposal = False """
    
    
    """ def _set_website_menu(self):
        for event in self:
            event.website_track_proposal_ok = event.website_track_proposal
            event.website_track_ok = event.website_track
            event.website_registration_ok = event.website_registration
            if event.menu_id and not event.website_menu:
                event.menu_id.unlink()
            elif event.website_menu:
                if not event.menu_id:
                    root_menu = self.env['website.menu'].create({'name': event.name})
                    event.menu_id = root_menu

                existing_page_names = event.menu_id.child_id.mapped('base_name')
                required_page_names = [entry[0] for entry in self._get_menu_entries()]
                standard_page_names = self._get_standard_menu_entries_names()

                # remove entries that should not exist anymore
                submenu_to_delete = event.menu_id.child_id.filtered(lambda menu: menu.base_name not in required_page_names and menu.base_name in standard_page_names)
                submenu_to_delete.unlink()

                # create missing entries
                
                for sequence, (name, url, xml_id, icon) in enumerate(self._get_menu_entries()):
                    if name not in existing_page_names:
                        if not url:
                            newpath = self.env['website'].new_page(name + ' ' + self.name, template=xml_id, ispage=False)['url']
                            url = "/event/" + slug(self) + "/page/" + newpath[1:]
                        created = self.env['website.menu'].create({
                            'name': name,
                            'base_name': name,
                            'url': url,
                            'icon': icon,
                            'parent_id': event.menu_id.id,
                            'sequence': sequence,
                        })
                        
                        trans = {
                                    'Introduction': 'Convocatoria',
                                    'Location':'Ubicación',
                                    'Register': 'Registro',
                                    'Talks': 'Presentaciones',
                                    'Agenda': 'Calendario',
                                    'Talk Proposals': 'Subir un trabajo'
                                }

                        self.env['ir.translation'].create({
                            'name': 'website.menu,name',
                            'res_id': created.id,
                            'lang': 'es_ES',
                            'type': 'model',
                            'src': created.name,
                            'value': trans.get(created.name, created.name),
                            'state': 'translated'
                        })
    """

    """
    def _get_menu_entries(self):
        self.ensure_one()
        res = [
            ('Introduction', '/event/%s/intro' % slug(self), False, 'fa fa-bullhorn')            
        ]
        if self.website_registration:
            res.append(('Register', '/event/%s/register' % slug(self), False, 'fa fa-shopping-cart'))
        if self.website_track:
            res += [
                ('Presentations', '/event/%s/track' % slug(self), False, 'fa fa-slideshare'),
                ('Agenda', '/event/%s/agenda' % slug(self), False, 'fa fa-calendar')]
        if self.website_track_proposal:
            res += [('Upload a paper', '/event/%s/track_proposal' % slug(self), False, 'fa fa-upload')]
        return res
    """

    @api.model
    def create(self, vals):
        if not vals.get('image_1920', False):
            img_path = get_module_resource('website_event_track_uclv', 'static/src/img', 'default-event.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            vals['image_1920'] = base64.b64encode(image)
        return super(Event, self).create(vals)
    
    def write(self, vals):
        group = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group.sudo().users:
            if  self.user_id.id != self.env.user.id:
                raise exceptions.Warning("You are not authorized to change this event")
        
        return super(Event, self).write(vals)
