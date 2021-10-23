from odoo import api, fields, models, _
from odoo.tools import float_utils


class AttendeeListReport(models.AbstractModel):
    _name = 'report.website_event_track_uclv.report_attendee_list'
    _description = "Attendee List Report"
    
    @api.model
    def get_attendees(self, event_ids, ticket_ids, pricelist_ids, only_unpaid):
        domain = [('state', '!=', 'cancel')]
        if only_unpaid:
            domain.append(('balance', '!=', 0))
        
        if len(event_ids) > 1:
            domain.append(('event_id', 'in', tuple(event_ids)))
        if len(event_ids) == 1:
            domain.append(('event_id', '=', event_ids[0]))
        
        if len(ticket_ids) > 1:
            domain.append(('event_ticket_id.product_id', 'in', tuple(ticket_ids)))
        if len(ticket_ids) == 1:
            domain.append(('event_ticket_id.product_id', '=', ticket_ids[0]))
        
        if len(pricelist_ids) > 1:
            domain.append(('pricelist_id', 'in', tuple(pricelist_ids)))
        if len(pricelist_ids) == 1:
            domain.append(('pricelist_id', '=', pricelist_ids[0]))
        
        return self.env['event.registration'].search(domain, order="id asc")

    @api.model
    def get_events(self, event_ids):
        if not event_ids:
            return [_('All events')]
        events = self.env["event.event"].search([('id', 'in', event_ids)])
        res = []
        for e in events:
            res.append(e.name + ' - ' + e.subname)

        return res
    
    @api.model
    def get_tickets(self, ticket_ids):
        if not ticket_ids:
            return [_('All tickets')]
        tickets = self.env["product.product"].search([('id', 'in', ticket_ids)])
        res = []
        for t in tickets:
            res.append(t.name)

        return res

    @api.model
    def get_pricelists(self, pricelist_ids):
        if not pricelist_ids:
            return [_('All pricelists')]
        pricelists = self.env["product.pricelist"].search([('id', 'in', pricelist_ids)])
        res = []
        for p in pricelists:
            res.append(p.name)

        return res

    @api.model
    def get_report_values(self, docids, data=None):
        event_ids = data['form']['event_ids']
        ticket_ids = data['form']['ticket_ids']
        pricelist_ids = data['form']['pricelist_ids']
        only_unpaid = data['form']['only_unpaid']
        #group_by_location = data['form']['group_by_location']

        return {
            'data': data,
            'events': self.get_events(event_ids),
            'tickets': self.get_tickets(ticket_ids),
            'pricelists': self.get_pricelists(pricelist_ids),
            'date': fields.Datetime.now(),
            'attendees': self.get_attendees(event_ids, ticket_ids, pricelist_ids, only_unpaid)

        }