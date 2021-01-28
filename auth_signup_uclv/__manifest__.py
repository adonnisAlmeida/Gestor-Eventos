# -*- coding: utf-8 -*-

{
    'name': 'UCLV Signup',
    'author': "Yerandy Reyes Fabregat (yerandy.reyes@desoft.cu)",
    'description': """
UCVL mods to auth_signup module
===============================
    """,
    'sequence': 101,
    'version': '1.0',
    'category': 'UCLV',
    'depends': [
        'base_uclv', 'auth_signup'
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/auth_signup_login_templates.xml',
    ],
    'bootstrap': True,
}
