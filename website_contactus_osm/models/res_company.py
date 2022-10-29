# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"
    
    osm_bbox = fields.Char("OpenStreetMap Box", related='partner_id.osm_bbox')
    osm_marker = fields.Char("OpenStreetMap Marker", related='partner_id.osm_marker')
    
    
    def osm_iframe_by_pos(self):
        partner = self.sudo().partner_id
        return partner and partner.osm_iframe_by_pos() or None    
    

    
