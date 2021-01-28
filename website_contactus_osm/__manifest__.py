# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'OSM Contact Us',
    'author': "Yerandy Reyes Fabregat (yerandy.reyes@desoft.cu)",
    'category': 'Website',
    'sequence': 50,
    'summary': 'Use OpenStreetMap in Contact Us',
    'website': 'https://www.odoo.com/page/website-builder',
    'version': '1.0',
    'description': "",
    'depends': ['website'],
    'installable': True,
    'data': [        
        'views/website_templates.xml',
        'views/res_company_views.xml',        
    ],
    'application': False,
}
