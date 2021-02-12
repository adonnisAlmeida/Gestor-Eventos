# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import ValidationError


class EventRegistrationPayment(models.Model):
    _name = 'event.registration.payment'
    _order = 'payment_date desc'

    def _get_default_date(self):
        return datetime.today()

    payment_date = fields.Datetime("Payment Date", required=True, default=_get_default_date)
    event_registration_id = fields.Many2one("event.registration", string="Attendee", required=True)
    amount = fields.Monetary("Amount", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="event_registration_id.currency_id")
    payment_type = fields.Selection([('cash', 'Cash'),('check', 'Check'),('transfer', 'Wire Transfer'),('online', 'Online')], string="Type", default="cash")
    reference = fields.Char("Reference")
        
    @api.constrains('payment_date')
    def _check_payment_date(self):
        if self.payment_date > datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            raise ValidationError(_('Payment date can not be later than now.'))


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
        amount = 0
        payment_ids = self.env['event.registration.payment'].search([('event_registration_id', '=', self.id)], order="payment_date asc")
        self.paid = False
        self.paid_date = False
        self.final_price = self.event_ticket_id.product_id.price
        
        if self.event_ticket_id:
            if not self.event_ticket_id.price:
                self.paid = True

        for payment in payment_ids:            
            amount += payment.amount
            if amount >= self.event_ticket_id.product_id.with_context(date=payment.payment_date).price:
                self.paid = True
                self.paid_date = payment.payment_date
                self.final_price = self.event_ticket_id.product_id.with_context(date=payment.payment_date).price

        self.balance = self.final_price - amount
    
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
            

    event_id = fields.Many2one("event.event", string="Event", required=True)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist", required=True)
    event_ticket_id = fields.Many2one("event.event.ticket", string="Event Ticket", required=True)
    payment_ids = fields.One2many("event.registration.payment", "event_registration_id", string="Payments")
    payment_count = fields.Integer(compute="get_payment_count")
    country_id = fields.Many2one("res.country", string="Country", required=True, default=_get_default_country)
    institution = fields.Char('Institution')
    gender = fields.Selection([('m','Male'),('f','Female'), ('u', 'Undefined')], 'Gender', default='u')
    currency_id = fields.Many2one('res.currency', string="Currency", related="pricelist_id.currency_id", readonly=True)
    
    balance = fields.Monetary(compute="get_balance", store=True)
    final_price = fields.Monetary("Price", compute="get_balance", store=True)
    paid = fields.Boolean("Is Paid?", compute="get_balance", store=True)
    paid_date = fields.Datetime("Payment Date", compute="get_balance", store=True)

    