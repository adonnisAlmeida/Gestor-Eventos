# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'UCLV Advanced Events',
    'author': "Yerandy Reyes Fabregat (yerandy.reyes@desoft.cu)",
    'category': 'UCLV',
    'summary': 'UCLV Sponsors, Tracks, Agenda, Event News',
    'website': 'https://www.odoo.com/page/events',
    'version': '1.0',
    'description': "",
    'sequence': 130,
    'depends': ['base_uclv', 'website_event_uclv', 'website_event_track', 'website_event_sale_uclv', 'portal_uclv', 'auth_signup_uclv'],
    'data': [
        'security/website_event_track_uclv_security.xml',
        'security/ir.model.access.csv',
        'data/event_track_data.xml',
        'views/assets.xml',
        'views/event_track_templates.xml',
        'views/event_track_review_views.xml',
        'views/event_reviewer_views.xml',
        'views/event_track_views.xml',
        'views/event_views.xml',
        'views/portal_reviews_templates.xml',
        'views/portal_papers_templates.xml',
        'views/event_checkpoint_templates.xml',
        'views/event_authenticity_templates.xml',
        'views/res_partner_views.xml',
        'report/report_event_track_analysis.xml',
        'report/report_event_attendee_analysis.xml',
        'wizard/attendee_list_wizard_view.xml',
        'wizard/attendee_create_wizard_view.xml',
        'report/event_registration_certificate_templates.xml',
        'report/event_track_templates.xml',
        'report/event_track_certificate_templates.xml',
        'report/event_track_certificate_templates2.xml',
        'report/event_track_certificate_templates3.xml',
        'report/event_track_certificate_templates4.xml',
        'report/reports.xml',
        'report/attendee_list_templates.xml',
    ]
}
