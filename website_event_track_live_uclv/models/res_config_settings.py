# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    avideo_base_domain = fields.Char(string='AVideo base domain')
    avideo_user = fields.Char(string='AVideo user')
    avideo_password = fields.Char(string='AVideo password') 

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        Params = self.env['ir.config_parameter'].sudo()
        res.update({
            'avideo_base_domain': '%s/' % Params.get_param('avideo.base.domain', default='https://video-convencion.uclv.cu'),
            'avideo_user': '%s' % Params.get_param('avideo.user', default='admin'),
            'avideo_password': '%s' % Params.get_param('avideo.password', default='2eb4f990fe8fdf3c847e4b8cc44461bb'),
        })
        return res
        

    def set_values(self):        
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("avideo.base.domain", self.avideo_base_domain or '')
        self.env['ir.config_parameter'].set_param("avideo.user", self.avideo_user or '')
        self.env['ir.config_parameter'].set_param("avideo.password", self.avideo_password or '')
