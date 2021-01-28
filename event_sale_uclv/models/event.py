# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero



class EventTicket(models.Model):
    _inherit = 'event.event.ticket'
    _description = 'Event Ticket'

    requires_approved_track_to_buy = fields.Boolean("Requires approved track to buy", default=True)
    requires_other_ticket_to_buy = fields.Boolean("Requires other ticket to buy", default=False)
    required_ticket_ids = fields.Many2many('event.event.ticket','event_event_ticket_event_event_ticket_rel','ticket_id', 'required_ticket_id')
    allowed_pricelist_ids = fields.Many2many("product.pricelist", "event_event_ticket_allowed_pricelist_rel", "event_ticket_id", "product_price_list_id", string="Allowed Pricelists")

    def is_allowed(self, pricelist):
        if pricelist in self.allowed_pricelist_ids:
            return True

        return False

    def can_buy(self, event):
        self.ensure_one()
        if self.requires_other_ticket_to_buy:
            # we don't allow public user to see buyed label
            if self.env.user != self.env.ref('base.public_user'):
                accepted_stages = [s.id for s in self.env["event.track.stage"].sudo().search([('is_done', '=', True)])]
                email = self.env.user.partner_id.email
                required_ticket_ids = [t.id for t in self.required_ticket_ids]
                domain = ['&', '|', ('email', '=', email), ('partner_id', '=', self.env.user.partner_id.id), ('event_id', '=', event.id), ('event_ticket_id', 'in', required_ticket_ids)]
                return self.env['event.registration'].sudo().search_count(domain) and (True, '') or (False, _('You need to buy other ticket in order to buy this item'))
            
            return False, _('Login to buy this item')
        if self.requires_approved_track_to_buy:
            # we don't allow public user to see buyed label
            if self.env.user != self.env.ref('base.public_user'):                
                accepted_stages = [s.id for s in self.env["event.track.stage"].sudo().search([('is_done', '=', True)])]               
                
                domain = [('partner_id', '=', self.env.user.partner_id.id), ('event_id', '=', event.id), ('stage_id', 'in', accepted_stages)]
                
                return self.env['event.track'].sudo().search_count(domain) and (True, '') or (False, _('You need an accepted track to buy this item'))
            
            return False, _('Login to buy this item')
        if self.env.user == self.env.ref('base.public_user'):
            return False, _('Login to buy this item')
        
        return True, ''

    def get_buyed(self, event):
        self.ensure_one()
        # we don't allow public user to see buyed label
        if self.env.user != self.env.ref('base.public_user'):
            email = self.env.user.partner_id.email
            domain = ['&', '|', ('email', '=', email), ('partner_id', '=', self.env.user.partner_id.id), ('event_id', '=', event.id), ('event_ticket_id', '=', self.id)]
            return self.env['event.registration'].sudo().search_count(domain)
        
        return 0
        
    def _default_product_id(self):
        return self.env.ref('event_sale.product_product_event', raise_if_not_found=False)

    name = fields.Char(string='Name', required=True, translate=True)
    
    

    event_type_id = fields.Many2one('event.type', string='Event Category', ondelete='cascade')
    event_id = fields.Many2one('event.event', string="Event", ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product',
        required=True, domain=[("event_ok", "=", True)],
        default=_default_product_id)
    registration_ids = fields.One2many('event.registration', 'event_ticket_id', string='Registrations')
    price = fields.Float(string='Price', digits='Product Price')
    deadline = fields.Date(string="Sales End")
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_is_expired')

    price_reduce = fields.Float(string="Price Reduce", compute="_compute_price_reduce", digits='Product Price')
    price_reduce_taxinc = fields.Float(compute='_get_price_reduce_tax', string='Price Reduce Tax inc')
    # seats fields
    seats_availability = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')],
        string='Available Seat', required=True, store=True, compute='_compute_seats', default="limited")
    seats_max = fields.Integer(string='Maximum Available Seats',
       help="Define the number of available tickets. If you have too much registrations you will "
            "not be able to sell tickets anymore. Set 0 to ignore this rule set as unlimited.")
    seats_reserved = fields.Integer(string='Reserved Seats', compute='_compute_seats', store=True)
    seats_available = fields.Integer(string='Available Seats', compute='_compute_seats', store=True)
    seats_unconfirmed = fields.Integer(string='Unconfirmed Seat Reservations', compute='_compute_seats', store=True)
    seats_used = fields.Integer(compute='_compute_seats', store=True)

    def _compute_is_expired(self):
        for record in self:
            if record.deadline:
                current_date = fields.Date.context_today(record.with_context({'tz': record.event_id.date_tz}))
                record.is_expired = record.deadline < current_date
            else:
                record.is_expired = False

    
    def _compute_price_reduce(self):
        for record in self:
            product = record.product_id
            discount = product.lst_price and (product.lst_price - product.price) / product.lst_price or 0.0
            record.price_reduce = (1.0 - discount) * record.price

    def _get_price_reduce_tax(self):
        for record in self:
            # sudo necessary here since the field is most probably accessed through the website
            tax_ids = record.sudo().product_id.taxes_id.filtered(lambda r: r.company_id == record.event_id.company_id)
            taxes = tax_ids.compute_all(record.price_reduce, record.event_id.company_id.currency_id, 1.0, product=record.product_id)
            record.price_reduce_taxinc = taxes['total_included']

    
    @api.depends('seats_max', 'registration_ids.state')
    def _compute_seats(self):
        """ Determine reserved, available, reserved but unconfirmed and used seats. """
        # initialize fields to 0 + compute seats availability
        for ticket in self:
            ticket.seats_availability = 'unlimited' if ticket.seats_max == 0 else 'limited'
            ticket.seats_unconfirmed = ticket.seats_reserved = ticket.seats_used = ticket.seats_available = 0
        # aggregate registrations by ticket and by state
        if self.ids:
            state_field = {
                'draft': 'seats_unconfirmed',
                'open': 'seats_reserved',
                'done': 'seats_used',
            }
            query = """ SELECT event_ticket_id, state, count(event_id)
                        FROM event_registration
                        WHERE event_ticket_id IN %s AND state IN ('draft', 'open', 'done')
                        GROUP BY event_ticket_id, state
                    """
            self.env.cr.execute(query, (tuple(self.ids),))
            for event_ticket_id, state, num in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket[state_field[state]] += num
        # compute seats_available
        for ticket in self:
            if ticket.seats_max > 0:
                ticket.seats_available = ticket.seats_max - (ticket.seats_reserved + ticket.seats_used)

    
    @api.constrains('registration_ids', 'seats_max')
    def _check_seats_limit(self):
        for record in self:
            if record.seats_max and record.seats_available < 0:
                raise ValidationError(_('No more available seats for the ticket'))

    @api.constrains('event_type_id', 'event_id')
    def _constrains_event(self):
        if any(ticket.event_type_id and ticket.event_id for ticket in self):
            raise UserError(_('Ticket should belong to either event category or event but not both'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.price = self.product_id.list_price or 0


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    event_ticket_id = fields.Many2one('event.event.ticket', string='Event Ticket')
    # in addition to origin generic fields, add real relational fields to correctly
    # handle attendees linked to sales orders and their lines
    # TDE FIXME: maybe add an onchange on sale_order_id + origin
    sale_order_id = fields.Many2one('sale.order', string='Source Sales Order', ondelete='cascade')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sales Order Line', ondelete='cascade')

    
    @api.constrains('event_ticket_id', 'state')
    def _check_ticket_seats_limit(self):
        for record in self:
            if record.event_ticket_id.seats_max and record.event_ticket_id.seats_available < 0:
                raise ValidationError(_('No more available seats for this ticket'))

    
    def _check_auto_confirmation(self):
        res = super(EventRegistration, self)._check_auto_confirmation()
        if res:
            orders = self.env['sale.order'].search([('state', '=', 'draft'), ('id', 'in', self.mapped('sale_order_id').ids)], limit=1)
            if orders:
                res = False
        return res

    @api.model
    def create(self, vals):
        res = super(EventRegistration, self).create(vals)
        if res.origin or res.sale_order_id:
            res.message_post_with_view('mail.message_origin_link',
                values={'self': res, 'origin': res.sale_order_id},
                subtype_id=self.env.ref('mail.mt_note').id)
        return res

    @api.model
    def _prepare_attendee_values(self, registration):
        """ Override to add sale related stuff """
        line_id = registration.get('sale_order_line_id')
        if line_id:
            registration.setdefault('partner_id', line_id.order_id.partner_id)
        att_data = super(EventRegistration, self)._prepare_attendee_values(registration)
        if line_id:
            att_data.update({
                'event_id': line_id.event_id.id,
                'event_id': line_id.event_id.id,
                'event_ticket_id': line_id.event_ticket_id.id,
                'origin': line_id.order_id.name,
                'sale_order_id': line_id.order_id.id,
                'sale_order_line_id': line_id.id,
            })
        return att_data

    
    def summary(self):
        res = super(EventRegistration, self).summary()
        if self.event_ticket_id.product_id.image_512:
            res['image'] = '/web/image/product.product/%s/image_512' % self.event_ticket_id.product_id.id
        information = res.setdefault('information', {})
        information.append((_('Name'), self.name))
        information.append((_('Ticket'), self.event_ticket_id.name or _('None')))
        order = self.sale_order_id.sudo()
        order_line = self.sale_order_line_id.sudo()
        if not order or float_is_zero(order_line.price_total, precision_digits=order.currency_id.rounding):
            payment_status = _('Free')
        elif not order.invoice_ids or any(invoice.state != 'paid' for invoice in order.invoice_ids):
            payment_status = _('To pay')
            res['alert'] = _('The registration must be paid')
        else:
            payment_status = _('Paid')
        information.append((_('Payment'), payment_status))
        return res