# -*- coding: utf-8 -*-

{
    'name': 'UCLV Events',
    'author': "Yerandy Reyes Fabregat (yerandy.reyes@desoft.cu)",
    'category': 'UCLV',
    'sequence': 120,
    'summary': 'Publish Events and Manage Online Registrations on your Website',
    'website': 'https://www.odoo.com/page/website-builder',
    'description': "",
    'depends': ['base_uclv', 'event_uclv', 'website_event', 'website_contactus_osm'],
    'installable': True,
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/event_templates.xml'
    ]
}
