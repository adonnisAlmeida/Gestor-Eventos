# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import controllers
from . import models
from . import wizard
from . import report
from odoo.api import Environment, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    stages = env['ir.model.data'].search([
        ('model', '=', 'event.track.stage'),
        ('module', '=', 'website_event_track'),
    ])
    for stage in stages:
        stage.write({'noupdate': False})