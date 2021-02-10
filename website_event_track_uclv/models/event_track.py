# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions
from odoo.tools.translate import _, html_translate
from odoo.addons.http_routing.models.ir_http import slug
from odoo import SUPERUSER_ID
import uuid


class TrackTag(models.Model):
    _name = "event.track.tag"
    _inherit = 'event.track.tag'
    
    def split(self):
        """splits into single words"""
        
        all_tags = self.env['event.track.tag'].search([('name','like',';')])
        delete_list = []
        for i in range(0, len(all_tags)):
            name = str(all_tags[i].name)
            words = name.split(';')
            tags = []
            for kw in words:
                kw = kw.strip()
                kw = kw.rstrip()
                #kw = kw.lower()
                if kw:
                    otags = self.env['event.track.tag'].search([('name', '=', kw)])
                    if not otags:
                        tag = self.env['event.track.tag'].create({'name': kw})
                        tags.append(tag)
                    else:
                        tags += otags            
            
            for tag in tags:
                for track in all_tags[i].track_ids:
                    tag.track_ids = [(4, track.id)]
            
            if all_tags[i] not in tags:
                delete_list.append(all_tags[i])
        
        for it in delete_list:
            it.unlink()
                
    
class TrackStage(models.Model):
    _name = 'event.track.stage'
    _inherit = 'event.track.stage'

    def validate(self, track):
        review_workflow = self.env['ir.config_parameter'].sudo().get_param('website_event_track_uclv.review_workflow') == 'True'
        if review_workflow:
            if self.id == 3: #accepted
                if not track.partner_id:
                    return False, _("You must assign an speaker to this track in order to set it in this state")
                if not track.recommendation or not track.recommendation2:
                    return False, _("You must assign reviewers recomendations to this track in order to set it in this state")
                track.website_published = True
            if self.id == 4: #scheduled
                if not track.location_id or not track.date:
                    return False, _("You must assign location and date to this track in order to set it in this state")
                track.website_published = True
            if self.id in (1, 5, 6):             
                track.website_published = False
            return True, ''
        else:
            if self.id == 3: #accepted
                track.website_published = True
            if self.id == 4: #scheduled
                track.website_published = True
            if self.id in (1, 5, 6):
                track.website_published = False
            return True, ''

    def pre_validate(self, track, vals):
        if self.id == 2: #review
            if not vals.get('partner_id', track.partner_id) or not vals.get('recommendation', track.recommendation) or not vals.get('recommendation2',track.recommendation2):
                return 2
            if vals.get('partner_id', track.partner_id) and vals.get('recommendation', track.recommendation) and vals.get('recommendation2', track.recommendation2):
                return 0
        if self.id == 3: #accepted
            if not vals.get('location_id', track.location_id) or not vals.get('date', track.date) or not vals.get('recommendation2',track.recommendation2):
                return 2
            if vals.get('location_id', track.location_id) and vals.get('date', track.recommendation) and vals.get('recommendation2', track.date):
                return 0
        
        return 1
        

class TrackType(models.Model):
    _name = 'event.track.type'
    name = fields.Char('Name', required=True, translate=True)
    description = fields.Char('Description', translate=True)


class TrackLocation(models.Model):
    _name = "event.track.location"
    _inherit = "event.track.location"    

    name = fields.Char('Room')
    partner_id = fields.Many2one('res.partner')
    
    _sql_constraints = [('name_uniq_partner', 'unique(name, partner_id)', _('Name must be unique by partner!'))]


class TrackAuthor(models.Model):
    _name = 'event.track.author'

    track_id = fields.Many2one('event.track', string="Track", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=1)

    _sql_constraints = [('track_uniq_partner', 'unique(track_id, partner_id)', _('Authors can only appear once per paper'))]


class TrackReview(models.Model):
    _name = 'event.track.review'
    _inherit = ['mail.thread']
    _description = "Paper Review"
    
    def _default_access_token(self):
        return uuid.uuid4().hex

    track_id = fields.Many2one('event.track', string="Track", required=True, ondelete='cascade')
    event_id = fields.Many2one('event.event', string="Event", related="track_id.event_id", store=True)
    name = fields.Char('Name', related="track_id.name")
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade', domain=[('email', '!=', '')])
    access_token = fields.Char('Invitation Token', default=_default_access_token)
    state = fields.Selection([('notice','Noticed'),('read','Readed'),('accept','Accepted'),('reject','Rejected'),('edit', 'Need changes'),('expired', 'Expired')], string="State", default="notice", required=True)

    @api.model
    def create(self, vals):        
        #send invitation email
        created = super(TrackReview, self).create(vals)
        template = self.env.ref('website_event_track_uclv.mail_template_reviewer_invitation', raise_if_not_found=False)
        if template:                    
            created.with_context(force_send=True).message_post_with_template(template.id)

        return created


class Track(models.Model):
    _name = "event.track"    
    _inherit = ['event.track', 'portal.mixin', 'mail.thread', 'mail.activity.mixin', 'website.seo.metadata', 'website.published.mixin']
    
       
    def _get_multiple(self):
        for item in self:
            if self.search_count([('name', '=', item.name),('event_id', '=', item.event_id.id)]) > 1:
                item.multiple = True
            else:
                item.multiple = False
    
    #Revision Stuffs
    coordinator_notes = fields.Text('Notes for the Coordinator')
    author_notes = fields.Text('Notes for the Author')
    recommendation = fields.Selection([('acceptwc', "Accepted With Changes"), ('acceptednc', "Accepted Without Changes"),  ('rejected', "Rejected")], 'Recommendation')
    coordinator_notes2 = fields.Text('Notes for the Coordinator')
    author_notes2 = fields.Text('Notes for the Author')
    recommendation2 = fields.Selection(
        [('acceptwc', "Accepted With Changes"), ('acceptednc', "Accepted Without Changes"), ('rejected', "Rejected")],
        'Recommendation')

    review_ids = fields.One2many('event.track.review', 'track_id', string='Reviews')
    address_id = fields.Many2one('res.partner', "Address", related="event_id.address_id", readonly=True)
    multiple = fields.Boolean("Multiple", compute="_get_multiple", store=True)
    track_type_id = fields.Many2one('event.track.type', "Track Type")
    publish_complete = fields.Boolean(string="Can be Published", default=True)
    
    user_id = fields.Many2one('res.users', related="event_id.user_id", string='Coordinator', readonly=True)
    
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'event.track')], string='Attachments')
    author_ids = fields.One2many('event.track.author', 'track_id', string='Authors')
    partner_id = fields.Many2one('res.partner', 'Speaker', required=True, domain=[('email', '!=', None)])
    partner_name = fields.Char('Speaker Name', related='partner_id.full_name')
    partner_email = fields.Char('Speaker Email', readonly=True, related='partner_id.email')
    email = fields.Char('Speaker Email', readonly=True, related='partner_id.email')
    partner_phone = fields.Char('Speaker Phone', readonly=True, related='partner_id.phone')
    partner_country = fields.Many2one('res.country','Speaker Country', readonly=True, related='partner_id.country_id')
    partner_institution = fields.Char('Speaker Institution', readonly=True, related='partner_id.institution')
    authenticity_url = fields.Char("Authenticity URL", compute="get_urls")
    authenticity_token = fields.Char("Authenticity Token")    
    description = fields.Html(translate=False, sanitize_attributes=False, sanitize_form=False)
    description_es = fields.Html(translate=False, sanitize_attributes=False, sanitize_form=False)
    is_done = fields.Boolean('Is Done', related="event_id.is_done", store=True)

    tag_ids = fields.Many2many('event.track.tag', string='Keywords')
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')], string='Kanban State',
        copy=False, default='blocked', required=True,
        help="A track's kanban state indicates special situations affecting it:\n"
             " * Grey is the default situation\n"
             " * Red indicates something is preventing the progress of this track\n"
             " * Green indicates the track is ready to be pulled to the next stage")
    language_id = fields.Many2one("res.lang", "Language")
    duration = fields.Float('Duration', default=0.25)
    image = fields.Binary('Image', related='partner_id.image_512', store=True, attachment=True)
    
    def build_uuids(self):
        regs = self.search([('authenticity_token', '=', False)])
        for reg in regs:
            reg.write({'authenticity_token': uuid.uuid1()})

    def get_urls(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for item in self:
            item.authenticity_url = base_url+'/events/auth/'+str(item.authenticity_token)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_biography = self.partner_id.website_description

    @api.model
    def create(self, vals):
        location_id = vals.get('location_id', False)
        if location_id:
            location = self.env['event.track.location'].browse(location_id)
            event = self.env['event.event'].browse(vals.get('event_id'))
            if location:
                if location.partner_id != event.address_id:
                    raise exceptions.Warning(_('Room is not valid for this event'))
        
        if not vals.get('authenticity_token', False):
            vals.update({'authenticity_token': uuid.uuid1()})
        
        return super(Track, self).create(vals)

        
    def write(self, vals):
        group = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group.sudo().users:
            if self.user_id.id != self.env.user.id and self.partner_id.user_id.id != self.env.user.id:
                raise exceptions.Warning(_("You are not authorized to change this track"))

        if 'stage_id' in vals and 'kanban_state' not in vals:
            vals['kanban_state'] = 'normal'        
              
        location_id = vals.get('location_id', self.location_id.id)
        if location_id:
            location = self.env['event.track.location'].browse(location_id)
            event = self.env['event.event'].browse(vals.get('event_id', self.event_id.id))
            if location:
                if location.partner_id != event.address_id:
                    raise exceptions.Warning(_('Room is not valid for this event'))
        

        #revision
        stage_id = vals.get('stage_id', self.stage_id.id)
        if stage_id:
            stage = self.env['event.track.stage'].browse(stage_id)
            res = stage.pre_validate(self, vals)
            if res == 2:
                vals.update({'kanban_state': 'blocked'})
            if res == 0:
                vals.update({'kanban_state': 'done'})
        
        stage_id = vals.get('stage_id', False)
        if stage_id:
            stage = self.env['event.track.stage'].browse(stage_id)
            res, err = stage.validate(self)
            if not res:
                raise exceptions.Warning(err)

        res = super(Track, self).write(vals)
        
        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])
        return res    
   

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        group1 = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group1.sudo().users:
            args += [("user_id", "=", self.env.user.id)]
        if name:
            recs = self.search([('name', 'ilike', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get() 

    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_domain = []
        group = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group.sudo().users:
            #new_domain.append(("user_id", "=", self.env.user.id))
            new_domain +=[("user_id", "=", self.env.user.id)]
        for arg in domain:
            new_domain.append(arg)
        return super(Track, self).read_group(new_domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
   
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        new_args = []
        group = self.env.ref('event_uclv.group_event_multimanager')
        if self.env.user not in group.sudo().users:
            #new_args.append(("user_id", "=", self.env.user.id))
            new_args += [("user_id", "=", self.env.user.id)]
        for arg in args:
            new_args.append(arg)

        return super(Track, self).search(new_args, offset=offset, limit=limit, order=order, count=count)


    