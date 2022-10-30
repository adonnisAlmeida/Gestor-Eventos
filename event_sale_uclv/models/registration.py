# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import ValidationError
import uuid


class EventRegistration(models.Model):
    _inherit = 'event.registration'
    _order = "create_date desc"
    
    def get_payment_count(self):
        self.payment_count = len(self.payment_ids)

    @api.onchange('event_id')
    def onchange_event_id(self):
        self.event_ticket_id = False

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        self.event_ticket_id = False

    @api.depends('payment_ids', 'payment_ids.amount', 'payment_ids.payment_date', 'event_ticket_id', 'event_ticket_id.product_id', 'event_ticket_id.product_id.price')
    def get_balance(self):
        for item in self:
            amount = 0
            payment_ids = self.env['event.registration.payment'].search([('event_registration_id', '=', self.id)], order="payment_date asc")
            item.paid = False
            item.paid_date = False
            item.final_price = item.event_ticket_id.product_id.price
            
            if item.event_ticket_id:
                if not item.event_ticket_id.price:
                    item.paid = True

            for payment in payment_ids:            
                amount += payment.amount
                if amount >= item.event_ticket_id.product_id.with_context(date=payment.payment_date).price:
                    item.paid = True
                    item.paid_date = payment.payment_date
                    item.final_price = item.event_ticket_id.product_id.with_context(date=payment.payment_date).price

            item.balance = item.final_price - amount
    
    def _get_default_country(self):
        return self.env.ref('base.cu').id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.email = self.partner_id.email
            self.institution = self.partner_id.institution
            self.gender = self.partner_id.gender
            if self.partner_id.country_id:
                self.country_id = self.partner_id.country_id.id

    def get_urls(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for item in self:
            item.authenticity_url = base_url+'/events/auth/'+str(item.authenticity_token)       

    event_id = fields.Many2one("event.event", string="Event", required=True)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist", required=False)
    event_ticket_id = fields.Many2one("event.event.ticket", string="Event Ticket", required=False)
    payment_ids = fields.One2many("event.registration.payment", "event_registration_id", string="Payments")
    payment_count = fields.Integer(compute="get_payment_count")
    country_id = fields.Many2one("res.country", string="Country", required=True, default=_get_default_country)
    institution = fields.Char('Institution')
    gender = fields.Selection([('m','Male'),('f','Female'), ('u', 'Undefined')], 'Gender', default='u')
    currency_id = fields.Many2one('res.currency', string="Currency", related="pricelist_id.currency_id", readonly=True)
    authenticity_url = fields.Char("Authenticity URL", compute="get_urls")
    authenticity_token = fields.Char("Authenticity Token")

    balance = fields.Monetary(compute="get_balance", store=True)
    final_price = fields.Monetary("Price", compute="get_balance", store=True)
    paid = fields.Boolean("Is Paid?", compute="get_balance", store=True)
    paid_date = fields.Datetime("Payment Date", compute="get_balance", store=True)

    @api.model
    def create(self, vals):
        if not vals.get('authenticity_token', False):
            vals.update({'authenticity_token': uuid.uuid4()})
        res = super(EventRegistration, self).create(vals)       
        return res

"""
class EventRegistration(models.Model):
    _inherit = 'event.registration'

    
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

        """
