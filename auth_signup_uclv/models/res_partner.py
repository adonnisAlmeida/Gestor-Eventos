# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.depends('name','title')
    def get_full_name(self):
        for partner in self:
            if partner.title and partner.title.shortcut:
                partner.full_name = partner.title.shortcut + " " + partner.name
            else:
                partner.full_name = partner.name

    institution = fields.Char('Institution')
    gender = fields.Selection([('m','Male'),('f','Female'), ('u', 'Undefined')], 'Gender', default='u')
    full_name = fields.Char('Full name', store=True, compute="get_full_name")
    reviewer = fields.Boolean("User wants to be reviewer", default=False)

    