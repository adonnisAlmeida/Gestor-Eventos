# -*- coding: utf-8 -*-
""""
Created on 21/05/2019
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models


class FlowExistenceWizard(models.TransientModel):
    _name = 'attendee.list.wizard'
    _description = 'Attendee List Wizard'

    event_ids = fields.Many2many("event.event", "attendee_list_event_rel", "wizard_id", "event_id", string="Events",  required=False)
    ticket_ids = fields.Many2many("product.product", "attendee_list_product_rel", "wizard_id", "product_id", string="Tickets",  required=False, domain=[('event_ok', '=', True)])
    pricelist_ids = fields.Many2many("product.pricelist", "attendee_list_pricelist_rel", "wizard_id", "pricelist_id", string="Pricelists", required=False)
    only_unpaid = fields.Boolean(string="Only unpaid", default=True)
    #group_by_location = fields.Boolean(string="Agrupar por ubicaciones", default=True)

    
    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'attendee.list.report',
            'form': self.read()[0]
        }
        return self.env.ref('website_event_track_uclv.action_report_attendee_list').report_action([], data=datas)