# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportEventAttendeeAnalysis(models.Model):
    _name = 'report.event.attendee.analysis'
    _auto = False

    event_name = fields.Char(string="Main Event", readonly=True, translate=True)
    event_id = fields.Many2one('event.event', string='Event', readonly=True)
    attendee_id = fields.Many2one('event.registration', string='Attendee', readonly=True)
    contact_id = fields.Many2one('res.partner', string='Contact', readonly=True)
    contact_user_id = fields.Many2one('res.users', string='User', readonly=True)
    contact_country_id = fields.Many2one('res.country', string='Contact Country', readonly=True)
    contact_institution = fields.Char(string='Contact Institution', readonly=True)
    contact_email = fields.Char(string='Contact Email', readonly=True)
    manager_id = fields.Many2one('res.users', string='Manager', readonly=True)
    ticket_id  = fields.Many2one('event.event.ticket', string='Ticket', readonly=True)
    attendee_state = fields.Char(string="State", readonly=True)
    attendee_paid = fields.Boolean(string="Is Paid?", readonly=True)
    attendee_balance = fields.Float(string="Debt", readonly=True)
    attendee_final_price = fields.Float(string="Price", readonly=True)
    paid_amount = fields.Float(string="Paid", readonly=True)
    date_open = fields.Datetime(string="Registration Date", readonly=True)
    paid_date = fields.Datetime(string="Payment Date", readonly=True)
    date_closed = fields.Datetime(string="Attended Date", readonly=True)

    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_event_attendee_analysis')
        self._cr.execute("""CREATE or REPLACE VIEW report_event_attendee_analysis AS (
                 SELECT
                        attendee.id as id,
                        attendee.state as attendee_state,
                        attendee.paid as attendee_paid,
                        attendee.date_open as date_open,
                        attendee.paid_date as paid_date,
                        attendee.date_closed as date_closed,
                        attendee.final_price as attendee_final_price,
                        attendee.balance as attendee_balance,
                        attendee.id as attendee_id,
                        sum(attendee.final_price - attendee.balance) as paid_amount,
                        event.id as event_id,
                        event.name as event_name,
                        contact.id as contact_id,
                        contact_user.id as contact_user_id,
                        country.id as contact_country_id,
                        resp.id as manager_id,
                        ticket.id as ticket_id,
                        contact.institution as contact_institution,
                        contact.email as contact_email
                    FROM
                        event_registration attendee
                        LEFT JOIN event_event event ON (attendee.event_id=event.id)
                        LEFT JOIN res_partner contact ON (attendee.partner_id=contact.id)
                        LEFT JOIN res_country country ON (contact.country_id=country.id)
                        LEFT JOIN res_users resp ON (event.user_id=resp.id)
                        LEFT JOIN res_users contact_user ON (contact_user.partner_id=contact.id)
                        LEFT JOIN event_event_ticket ticket ON (attendee.event_ticket_id=ticket.id)
                    WHERE true
                    GROUP BY
			            event.id,
                        event.name,
                        attendee.id,
                        attendee.state,
                        attendee.paid,
                        contact_user.id,
                        contact.id,
                        contact.institution,
                        contact.email,
                        country.id,
                        resp.id,
                        ticket.id,
                        attendee.date_open,
                        attendee.paid_date,
                        attendee.date_closed
                )""")
