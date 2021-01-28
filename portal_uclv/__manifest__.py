{
    'name': 'UCLV Portal',
    'version': '14.0.1.0',
    'author': 'Yerandy Reyes',
    'maintainer': 'Yerandy Reyes',    
    'license': 'AGPL-3',
    'category':  'Website',
    'summary': 'This module allows portal user to add/change/delete his avatar (profile picture).',
    'description':
        """This module allows portal user to add/change/delete his avatar (profile picture).
        """,
    'depends': ['base_uclv', 'portal', 'website_profile'],
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'views_inherited/ir_qweb_widget_templates.xml',
        'views_inherited/portal_templates.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
