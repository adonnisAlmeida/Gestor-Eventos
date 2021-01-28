# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug

from odoo import api, models, fields


def urlplus(url, params):
    return werkzeug.Href(url)(params or None)


class Partner(models.Model):

    _inherit = "res.partner"

    osm_bbox = fields.Char("OpenStreetMap Box")
    osm_marker = fields.Char("OpenStreetMap Marker")

    
    def osm_iframe_by_name_address(self):        
        params = {
            'q': '%s, %s %s, %s' % (self.street or '', self.city or '', self.zip or '', self.country_id and self.country_id.name_get()[0][1] or ''),
            'format': "html",
            'polygon': 1,
            'addressdetails': 1
        }
        return urlplus('https://nominatim.openstreetmap.org/search', params)

    
    
    def osm_iframe_by_pos(self):
        if not self.osm_bbox:
            return False
        params = {
            'bbox': self.osm_bbox,
            'marker': self.osm_marker,
            'layer': 'mapnik',
        }
        return urlplus('https://www.openstreetmap.org/export/embed.html', params)
    