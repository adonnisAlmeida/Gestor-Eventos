# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    updates_auto = fields.Boolean('Auto update')
    updates_frequency_hours = fields.Integer('Check updates every (hours)')
    updates_dir_url = fields.Char('Update URL')
    installed_version = fields.Char('Installed version', readonly=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        module = self.env['ir.module.module'].search([('name', '=', 'odoo_auto_updater')])
        installed_version = module[0].installed_version
        
        res.update({'updates_auto': bool(self.env['ir.config_parameter'].get_param("odoo_auto_updates.updates_auto")),
                    'updates_frequency_hours': int(self.env['ir.config_parameter'].get_param("odoo_auto_updates.updates_frequency_hours")),
                    'updates_dir_url': self.env['ir.config_parameter'].get_param("odoo_auto_updates.updates_dir_url"),
                    'installed_version': installed_version
                    })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("odoo_auto_updates.updates_auto", self.updates_auto)
        self.env['ir.config_parameter'].set_param("odoo_auto_updates.updates_frequency_hours", self.updates_frequency_hours)
        self.env['ir.config_parameter'].set_param("odoo_auto_updates.updates_dir_url", self.updates_dir_url)
        
        cron = self.env.ref("odoo_auto_updater.updater_cron")
        cron.write({'interval_number': self.updates_frequency_hours, 'active': self.updates_auto})
        
