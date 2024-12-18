# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions


class Track(models.Model):    
    _inherit = 'event.track'    
    
    def _avideo_base_domain(self):
        if self.avideo_url:
            self.avideo_base_domain = self.env['ir.config_parameter'].sudo().get_param('avideo.base.domain')
            if self.avideo_base_domain[:-1] != '/':
                self.avideo_base_domain +='/'
            self.avideo_full_url = self.avideo_base_domain +'video/'+self.avideo_url
        else:
            self.avideo_base_domain = "/"
            self.avideo_full_url = ""

    avideo_base_domain = fields.Char('AVideo URL', compute="_avideo_base_domain")
    avideo_url = fields.Char('AVideo URL')
    avideo_full_url = fields.Char('AVideo URL', compute="_avideo_base_domain")

    