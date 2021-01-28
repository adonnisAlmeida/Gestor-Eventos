# -*- coding: utf-8 -*-
{
    'name': 'UCLV Events Organization',
    'version': '1.0',
    'sequence': 110,
    'author': "Yerandy Reyes Fabregat (yerandy.reyes@desoft.cu)",
    'website': 'https://www.odoo.com/page/events',
    'category': 'UCLV',
    'summary': 'Trainings, Conferences, Meetings, Exhibitions, Registrations',
    'description': """
UCLV Organization and management of Events.
===========================================
""",
    'depends': ['base_uclv', 'event'],
    'data': [
        'security/event_security.xml',        
        'views/event_views.xml',
        'report/event_event_templates.xml',
        'report/event_reports.xml'
    ],
    'installable': True
}
