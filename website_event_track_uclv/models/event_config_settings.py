# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    event_review_workflow = fields.Boolean("Review Workflow")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({'event_review_workflow': self.env['ir.config_parameter'].get_param("website_event_track_uclv.review_workflow")=='True'})
        return res
    
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("website_event_track_uclv.review_workflow", self.event_review_workflow and 'True' or 'False')
        
        
        
        
