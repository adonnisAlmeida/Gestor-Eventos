# -*- encoding: utf-8 -*-
{
    'name': 'Odoo V11 Importer',
    'summary': 'Import data from v11 odoo db',
    'version': '14.0.1.',
    'category': 'Website',
    'author': 'Yerandy Reyes Fabregat <yerandy.reyes@desoft.cu>',
	'maintainer': 'Yerandy Reyes Fabregat <yerandy.reyes@desoft.cu>',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'wizard/manual_importer_wizard_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
