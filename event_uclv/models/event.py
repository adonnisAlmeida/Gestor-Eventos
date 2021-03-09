# -*- coding: utf-8 -*-

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate
from odoo.modules import get_module_resource
import base64

from dateutil.relativedelta import relativedelta
try: 
    import qrcode
except ImportError:
    qrcode = None


class EventEvent(models.Model):
    """Event"""
    _name = "event.event"
    _inherit = ['event.event', 'image.mixin'] 

    

    parent_id = fields.Many2one('event.event', string="Parent Event", domain="[('is_meta_event', '=', True)]")
    children_ids = fields.One2many('event.event', 'parent_id', string="Children Events")
    is_meta_event = fields.Boolean(string="Is Meta Event", default=False)    

    short_name = fields.Char(
        string='Event Short Name', translate=True, required=False,
        readonly=False)
    subname = fields.Char(
        string='Event Sub Name', translate=True, required=False,
        readonly=False)
    number = fields.Char("Number")
    user_id = fields.Many2one('res.users', string='Manager', required=True)
    
    @api.depends('name', 'short_name', 'subname', 'date_begin', 'date_end')
    def name_get(self):
        result = []
        for event in self:
            name = event.name
            if event.short_name:
                name += ' "' + event.short_name + '"'
            if event.subname:
                name += ' -' + event.subname
            result.append((event.id, '%s' % (name)))
        return result

    url = fields.Char("URL", compute="get_url")
    
    def get_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for item in self:
            item.url = base_url+'/event/'+str(item.id)
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        new_args = []
        if not self.env.context.get('website_id'):
            if self.env.user.has_group('event.group_event_manager'):
                new_args.append((1, "=", 1))
            elif self.env.user.has_group('event.group_event_user'):
                new_args+=['|', '&', ("user_id", "=", self.env.user.id),('is_meta_event','=', True),('is_published','=', True)]
        
        for arg in args:
            new_args.append(arg)
        return super(EventEvent, self).search(new_args, offset=offset, limit=limit, order=order, count=count)    
        
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()        
        if not self.env.context.get('website_id'):
            if self.env.user.has_group('event.group_event_manager'):
                args.append((1, "=", 1))
            elif self.env.user.has_group('event.group_event_user'):
                args+=['|', '&', ("user_id", "=", self.env.user.id),('is_meta_event','=', True),('is_published','=', True)]
        if name:
            recs = self.search(['|','|', ('name', 'ilike', name),('short_name', 'ilike', name), ('subname', 'ilike', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_domain = []
        if not self.env.context.get('website_id'):
            if self.env.user.has_group('event.group_event_manager'):
                new_domain.append((1, "=", 1))
            elif self.env.user.has_group('event.group_event_user'):
                new_domain.append(("user_id", "=", self.env.user.id))
        for arg in domain:
            new_domain.append(arg)
        return super(EventEvent, self).read_group(new_domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def create(self, vals):
        if not vals.get('image_1920', False):
            img_path = get_module_resource('event_uclv', 'static/src/img', 'default-event.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            vals['image_1920'] = base64.b64encode(image)
        return super(EventEvent, self).create(vals)

    @api.depends('event_ticket_ids.sale_available')
    def _compute_event_registrations_sold_out(self):
        for event in self:
            if event.seats_limited and not event.seats_available and event.seats_max:
                event.event_registrations_sold_out = True
            elif event.event_ticket_ids:
                event.event_registrations_sold_out = not any(
                    ticket.seats_available > 0 if ticket.seats_limited else True for ticket in event.event_ticket_ids
                )
            else:
                event.event_registrations_sold_out = False


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    url = fields.Char("URL", compute="get_url")
    passport = fields.Char("Passport or ID")

    def get_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for item in self:
            item.url = base_url+'/event/registration/'+str(item.id)

    #TODO : enable this when sale addon is ready
    """@api.model
    def create(self, vals):
        if self.search_count([
            ('name', '=', vals.get('name')),
            ('passport', '=', vals.get('passport')),
            ('event_id', '=', vals.get('event_id')),
            ('partner_id', '=', vals.get('partner_id')),
            #('event_ticket_id', '=', vals.get('event_ticket_id')),
            ('state', 'not in', ('cancel',)),
            ]):
            raise ValidationError('Attendee "%s" is already registered for this event. If you want to register it using another ticket, you must cancel its registration first.' % vals.get('name'))
        vals.update({'state': 'draft'})
        return super(EventRegistration, self).create(vals)"""
    
    