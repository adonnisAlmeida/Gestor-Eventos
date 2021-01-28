# -*- coding: utf-8 -*-

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

from dateutil.relativedelta import relativedelta
try: 
    import qrcode
except ImportError:
    qrcode = None

class EventEvent(models.Model):
    """Event"""
    _name = "event.event"
    _inherit = ['event.event', 'image.mixin'] 

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
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()       
        if name:
            recs = self.search(['|','|', ('name', 'ilike', name),('short_name', 'ilike', name), ('subname', 'ilike', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    url = fields.Char("URL", compute="get_url")
    passport = fields.Char("Passport or ID")

    def get_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for item in self:
            item.url = base_url+'/event/registration/'+str(item.id)

    @api.model
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
        return super(EventRegistration, self).create(vals)
    
    