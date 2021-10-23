# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import ValidationError


class EventRegistrationPayment(models.Model):
    _name = 'event.registration.payment'
    _description = "Registration Payment"
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

