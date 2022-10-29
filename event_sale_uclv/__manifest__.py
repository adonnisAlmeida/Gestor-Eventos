# -*- coding: utf-8 -*-

{
    'name': 'UCLV Events Sales',
    'version': '1.1',
    'category': 'UCLV',
    'sequence': 111,
    'website': 'https://www.odoo.com/page/events',
    'description': """
""",
    'depends': ['event_sale', 'base_uclv'],
    'data': [
        'security/ir.model.access.csv',
        #'views/event_registration_payment_views.xml',
        'views/event_ticket_views.xml',
        'views/event_views.xml',
        'views/event_registration_views.xml',
        'views/res_partner_views.xml',
        'report/event_event_templates.xml'
    ],
    'installable': True,
    'auto_install': False
}
