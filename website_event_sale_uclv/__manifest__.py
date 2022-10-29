# -*- coding: utf-8 -*-

{
    'name': "UCLV Website Event Sale",
    'category': 'UCLV',
    'sequence': 140,
    'summary': "UCLV Manage Events and Sell Tickets Online",
    'website': 'https://www.odoo.com/page/events',
    'description': """
UCLV Online Event's Tickets
======================

        """,
    'depends': ['website_event_sale', 'event_sale_uclv'],
    'data': [
        "data/event_sale_data.xml",
        'views/event_templates.xml',
        'views/website_sale_templates.xml',
        'security/ir.model.access.csv',
        'security/website_event_sale_security.xml',
    ],
    'auto_install': False
}
