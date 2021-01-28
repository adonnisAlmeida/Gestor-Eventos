# -*- encoding: utf-8 -*-
{
    'name': 'Odoo Auto Updater',
    'summary': 'Updates modules automatically',
    'version': '14.0.1.20190204',
    'category': 'Website',
    'author': 'Yerandy Reyes Fabregat <yerandy.reyes@desoft.cu>',
	'maintainer': 'Yerandy Reyes Fabregat <yerandy.reyes@desoft.cu>',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'wizard/manual_updater_wizard_view.xml',        
        'views/res_config_settings_views.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
