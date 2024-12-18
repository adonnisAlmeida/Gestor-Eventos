# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Live Event Tracks UCLV',
    'category': 'Marketing/Events',
    'sequence': 1006,
    'version': '1.0',
    'summary': 'Support live tracks: streaming, participation, youtube',
    'website': 'https://www.odoo.com/page/events',
    'description': "",
    'depends': [
        'website_event_track_uclv',
        'website_event_track_live',
    ],
    'data': [
        'views/assets.xml',
        'views/res_config_settings.xml',
        'views/event_track_templates_page.xml',
        'views/event_track_templates_list.xml',
        'views/portal_papers_templates.xml',
    ],    
    'application': False,
    'installable': True,
}
