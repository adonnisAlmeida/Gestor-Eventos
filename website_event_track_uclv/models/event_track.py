# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions
from odoo.tools.translate import _, html_translate
from odoo.addons.http_routing.models.ir_http import slug
from odoo import SUPERUSER_ID
import uuid


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'access_token' not in vals and vals.get('res_model', False) == 'event.track':
                vals['access_token'] = self._generate_access_token()
        res_ids = super(IrAttachment, self).create(vals_list)
        return res_ids

        
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

    can_review = fields.Boolean(default=True)
    can_edit = fields.Boolean(default=True)
    requires_partner = fields.Boolean(default=True)
    requires_reviews = fields.Boolean(default=False)
    requires_location = fields.Boolean(default=False)
    requires_date = fields.Boolean(default=False)
    next_requires_partner = fields.Boolean(default=True)
    next_requires_reviews = fields.Boolean(default=False)
    next_requires_location = fields.Boolean(default=False)
    next_requires_date = fields.Boolean(default=False)
    publish = fields.Boolean(default=False)

    def kanban_validate(self, track):
        result = 'done'
        if self.next_requires_partner and not track.partner_id:
            result = 'blocked'
        if self.next_requires_reviews and not len(track.review_ids):
            result = 'blocked'
        if self.next_requires_location and not track.location_id:
            result = 'blocked'
        if self.next_requires_date and not track.date:
            result = 'blocked'
        return result

    def before_enter_validate(self, track):
        if track.event_id.strict_review_workflow:            
            if self.requires_partner and not track.partner_id:
                return False, _("You must assign an speaker to this track in order to set it in this stage")
            if self.requires_reviews and not len(track.review_ids):
                return False, _("You must assign reviewers to this track in order to set it in this stage")
            if self.requires_location and not track.location_id:
                return False, _("You must assign location to this track in order to set it in this stage")
            if self.requires_date and not track.date:
                return False, _("You must assign date to this track in order to set it in this stage")
        
        return True, ''


class TrackType(models.Model):
    _name = 'event.track.type'
    _description = 'Track Type'

    name = fields.Char('Name', required=True, translate=True)
    description = fields.Char('Description', translate=True)
    is_paper = fields.Boolean('Is paper', default=True)


class TrackLocation(models.Model):
    _name = "event.track.location"
    _inherit = "event.track.location"    

    def partner_default(self):
        return self.env.context.get('partner_id', False)

    name = fields.Char('Room')
    partner_id = fields.Many2one('res.partner', default=partner_default)
    
    _sql_constraints = [('name_uniq_partner', 'unique(name, partner_id)', _('Name must be unique by partner!'))]


class TrackAuthor(models.Model):
    _name = 'event.track.author'
    _description = 'Track Author'

    track_id = fields.Many2one('event.track', string="Track", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=1)

    _sql_constraints = [('track_uniq_partner', 'unique(track_id, partner_id)', _('Authors can only appear once per paper'))]


class TrackReview(models.Model):
    _name = 'event.track.review'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Paper Review"
    
    def _default_access_token(self):
        return uuid.uuid4().hex

    @api.depends('track_id', 'track_id.event_id','track_id.event_id.paper_abstract_notification_date')
    def _compute_expired(self):
        for item in self:
            item.expired = False
            if item.track_id.is_done:
                item.expired = True
            if item.track_id.event_id.paper_abstract_notification_date and item.track_id.event_id.paper_abstract_notification_date < fields.Date.today():
                item.expired = True

    track_id = fields.Many2one('event.track', string="Track", required=True, ondelete='cascade')
    event_id = fields.Many2one('event.event', string="Event", related="track_id.event_id", store=True)
    name = fields.Char('Name', related="track_id.name")
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete='cascade', domain=[('email', '!=', '')])
    access_token = fields.Char('Invitation Token', default=_default_access_token)
    state = fields.Selection([('notice','Noticed'),('read','Readed'),('accept','Accepted'),('reject','Rejected'),('edit', 'Need changes')], string="State", default="notice", required=True, tracking=True)
    weight = fields.Integer('Weight', default = 10)
    expired = fields.Boolean(string='Is expired', compute=_compute_expired)
    is_done = fields.Boolean(string='Is Done', related='track_id.is_done')

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
    
    def _track_template(self, changes):
        res = super(Track, self)._track_template(changes)
        track = self[0]
        if 'stage_id' in changes and track.stage_id.mail_template_id and not self.env.context.get('no_message'):
            res['stage_id'] = (track.stage_id.mail_template_id, {
                'composition_mode': 'comment',
                'auto_delete_message': True,
                'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                'email_layout_xmlid': 'mail.mail_notification_light'
            })        
        return res

    def _get_multiple(self):
        for item in self:
            if self.search_count([('name', '=', item.name),('event_id', '=', item.event_id.id)]) > 1:
                item.multiple = True
            else:
                item.multiple = False
    
    @api.depends('review_ids', 'review_ids.state')
    def _get_reviews_count(self):
        for item in self:
            item.reviews_count = 0
            item.reviews_accepted_count = 0
            item.reviews_edit_count = 0
            item.reviews_rejected_count = 0
            for review in item.review_ids:
                item.reviews_count += review.weight
                if review.state == 'accept':
                    item.reviews_accepted_count += review.weight
                if review.state == 'edit':
                    item.reviews_edit_count += review.weight
                if review.state == 'reject':
                    item.reviews_rejected_count += review.weight
    
    #Revision Stuffs
    manager_notes = fields.Text('Notes for the Manager')
    author_notes = fields.Text('Notes for the Author')
    recommendation = fields.Selection([('acceptwc', "Accepted With Changes"), ('acceptednc', "Accepted Without Changes"),  ('rejected', "Rejected")], 'Recommendation')
    manager_notes2 = fields.Text('Notes for the Manager')
    author_notes2 = fields.Text('Notes for the Author')
    recommendation2 = fields.Selection(
        [('acceptwc', "Accepted With Changes"), ('acceptednc', "Accepted Without Changes"), ('rejected', "Rejected")],
        'Recommendation')


    review_ids = fields.One2many('event.track.review', 'track_id', string='Reviews', tracking=True)
    reviews_count = fields.Integer(compute=_get_reviews_count, store=True)
    reviews_accepted_count = fields.Integer(compute=_get_reviews_count, store=True)
    reviews_edit_count = fields.Integer(compute=_get_reviews_count, store=True)
    reviews_rejected_count = fields.Integer(compute=_get_reviews_count, store=True)

    address_id = fields.Many2one('res.partner', "Address", related="event_id.address_id", readonly=True)
    multiple = fields.Boolean("Multiple", compute="_get_multiple", store=True)
    track_type_id = fields.Many2one('event.track.type', "Track Type")
    publish_complete = fields.Boolean(string="Can be Published", default=True)
    
    user_id = fields.Many2one('res.users', related="event_id.user_id", string='Manager', readonly=True)
    
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
            reg.write({'authenticity_token': uuid.uuid4()})

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
        event = self.env['event.event'].browse(vals.get('event_id'))
        if location_id:
            location = self.env['event.track.location'].browse(location_id)
            
            if location:
                if location.partner_id != event.address_id:
                    raise exceptions.Warning(_('Room is not valid for this event'))
        
        if not self.env.context.get('ignore_errors', False):
            date = vals.get('date', False)
            if date:            
                if date < event.date_begin.strftime("%Y-%m-%d %H:%M:%S") or date > event.date_end.strftime("%Y-%m-%d %H:%M:%S"):
                    raise exceptions.UserError(_("Track date must be between %s and %s") %(event.date_begin.strftime("%Y-%m-%d %H:%M:%S"), event.date_end.strftime("%Y-%m-%d %H:%M:%S") ))

        if not vals.get('authenticity_token', False):
            vals.update({'authenticity_token': uuid.uuid4()})

        #assign auto reviewers                
        created = super(Track, self).create(vals)
        
        for reviewer in created.event_id.reviewer_ids:
            if created.partner_id.state_id in reviewer.auto_partner_country_state.mapped('id'):
                self.env['event.track.review'].create({'track_id':created.id, 'partner_id': reviewer.partner_id.id, 'weight': reviewers.weight})
        
        return created

        
    def write(self, vals):
        if 'stage_id' in vals and 'kanban_state' not in vals:
            vals['kanban_state'] = 'normal'        
              
        location_id = vals.get('location_id', self.location_id.id)
        if location_id:
            location = self.env['event.track.location'].browse(location_id)
            event = self.env['event.event'].browse(vals.get('event_id', self.event_id.id))
            if location:
                if location.partner_id != event.address_id:
                    raise exceptions.Warning(_('Room is not valid for this event'))
        
        date = vals.get('date', self.date and self.date.strftime("%Y-%m-%d %H:%M:%S") or False)
        if date:
            if date < self.event_id.date_begin.strftime("%Y-%m-%d %H:%M:%S") or date > self.event_id.date_end.strftime("%Y-%m-%d %H:%M:%S"):
                raise exceptions.UserError(_("Track date must be between %s and %s") %(self.event_id.date_begin.strftime("%Y-%m-%d %H:%M:%S"),self.event_id.date_end.strftime("%Y-%m-%d %H:%M:%S") ))

        stage_id = vals.get('stage_id', self.stage_id.id)
        if stage_id:
            stage = self.env['event.track.stage'].browse(stage_id)
            vals.update({'kanban_state': stage.kanban_validate(self)})
        
        stage_id = vals.get('stage_id', False)
        if stage_id:
            stage = self.env['event.track.stage'].browse(stage_id)
            res, err = stage.before_enter_validate(self)
            if not res:
                raise exceptions.Warning(err)
            
            vals.update({'website_published': stage.publish})

        res = super(Track, self).write(vals)
                
        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        new_args = []
        if not self.env.context.get('website_id'):
            if self.env.user.has_group('event.group_event_manager'):
                new_args.append((1, "=", 1))
            elif self.env.user.has_group('event.group_event_user'):
                new_args.append(("event_id.user_id", "=", self.env.user.id))
        
        for arg in args:
            new_args.append(arg)
        return super(Track, self).search(new_args, offset=offset, limit=limit, order=order, count=count)    
        
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()        
        if not self.env.context.get('website_id'):
            if self.env.user.has_group('event.group_event_manager'):
                args.append((1, "=", 1))
            elif self.env.user.has_group('event.group_event_user'):
                args.append(("event_id.user_id", "=", self.env.user.id))
        if name:
            recs = self.search([('name', 'ilike', name)] + args, limit=limit)
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
                new_domain.append(("event_id.user_id", "=", self.env.user.id))
        for arg in domain:
            new_domain.append(arg)
        return super(Track, self).read_group(new_domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    