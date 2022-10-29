# -*- coding: utf-8 -*-
""""
Created on 21/06/2019
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models, exceptions


class AttendeeWizard(models.TransientModel):
    _name = 'event.registration.create.wizard'
    _description = 'Attendee Create Wizard'

    errors = fields.Text("Errors", readonly=True, default="")
    state = fields.Selection([('select', 'select'), ('done', 'done'), ('error', 'error')], default='select')

    def action_create(self):
        this = self[0]
        active_ids = self.env.context.get('active_ids', [])
        for active_id in active_ids:
            track = self.env['event.track'].browse(active_id)
            event = track.event_id
            country = track.partner_id.country_id or self.env.ref('base.cu')
            if country.code == 'CU':
                pricelist = self.env.ref('product.list0')
            else:
                pricelist = self.env.ref('event_sale_uclv.list1')
            
            event_tickets = self.env['event.event.ticket'].search([('event_id', '=', event.id),('allowed_pricelist_ids', 'in', pricelist.id)])
            if not event_tickets:
                raise exceptions.Warning("No hay posibles tickets para el evento %s y la tarifa %s" %(event.name_get()[0][1], pricelist.name))
            
            event_ticket = event_tickets[0]
            
            vals = {'partner_id': track.partner_id.id,
                    'name': track.partner_id.name,
                    'email': track.partner_id.email,
                    'institution': track.partner_id.institution,
                    'country_id': country.id,
                    'gender': track.partner_id.gender,
                    'event_id': event.id,
                    'pricelist_id': pricelist.id,
                    'event_ticket_id': event_ticket.id,
                    'currency_id': pricelist.currency_id.id,
                    'final_price': event_ticket.price,
                    'state': 'draft'
                    }
            try:
                created = self.env['event.registration'].create(vals)
                created.write({'state': 'draft'})
            except Exception as e:
                this.errors = str(this.errors) + str(e.name) + '\n'
        if this.errors:
            this.write({'state': 'error'})
        else:
            this.write({'state': 'done'})
        
        return {
            'type': 'ir.actions.act_window',                
            'name': 'Crear participante',
            'res_model': 'event.registration.create.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
    