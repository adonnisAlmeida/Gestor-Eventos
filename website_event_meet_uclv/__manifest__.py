# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'UCLV Event Meeting / Rooms',
    'category': 'Marketing/Events',
    'sequence': 1002,
    'version': '1.0',
    'summary': 'Event: meeting and chat rooms UCLV',
    'website': 'https://www.odoo.com/page/events',
    'description': "",
    'depends': [
        'website_event_uclv',
        'website_event_meet',
    ],    
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',        
        'views/event_meet_templates_list.xml',
        'views/event_meet_templates_page.xml',        
    ],
    'application': False,
    'installable': True,
}
