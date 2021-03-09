# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug


class Event(models.Model):
    _name = 'event.event'
    _order = 'number asc, id asc'
    _inherit = ['event.event', 'website.seo.metadata', 'website.published.mixin']

    @api.depends('children_ids', 'children_ids.is_published')
    def get_published_subevents_count(self):
        for item in self:
            item.published_subevents_count = 0
            for child in item.children_ids:
                if child.is_published:
                    item.published_subevents_count += 1
    published_subevents_count = fields.Integer(compute=get_published_subevents_count, store=True)
                    
    def _create_menu(self, sequence, name, url, xml_id, menu_type=False):
        """ If url: create a website menu. Menu leads directly to the URL that
        should be a valid route. If xml_id: create a new page, take its url back
        thanks to new_page of website, then link it to a menu. Template is
        duplicated and linked to a new url, meaning each menu will have its own
        copy of the template.

        :param menu_type: type of menu. Mainly used for inheritance purpose
          allowing more fine-grain tuning of menus. """
        if not url:
            self.env['ir.ui.view'].with_context(_force_unlink=True).search([('name', '=', name + ' ' + self.name)]).unlink()
            page_result = self.env['website'].sudo().new_page(name + ' ' + self.name, template=xml_id, ispage=False)
            url = "/event/" + slug(self) + "/page" + page_result['url']  # url contains starting "/"
        
        website_menu = self.env['website.menu'].sudo().create({
            'name': name,
            'url': url,
            'parent_id': self.menu_id.id,
            'sequence': sequence,
            'website_id': self.website_id.id,
        })
        #translations workaround
        t = {'Introduction': 'Introducción', 'Papers': 'Trabajos', 'Submit a paper': 'Subir un trabajo', 'Community': 'Comunidad', 'Agenda': 'Agenda', 'Exhibitors': 'Exhibidores'}
        translation = self.env['ir.translation'].search([('name', '=', 'website.menu,name'),('res_id', '=', website_menu.id),('lang', '=', 'es_ES')])
        if translation:
            translation.write({'value': t.get(translation.src, translation.value)})
        else:
            translation.create({
                'name': 'website.menu,name',
                'res_id':  website_menu.id,
                'lang': 'es_ES',
                'type': 'model',
                'state': 'translated',
                'value': t.get(translation.src, translation.value)
            })

        if menu_type:
            self.env['website.event.menu'].create({
                'menu_id': website_menu.id,
                'event_id': self.id,
                'menu_type': menu_type,
            })
        return website_menu

    def _get_website_menu_entries(self):
        self.ensure_one()
        return [           
            ('Introduction', '/event/%s/register' % slug(self), False, 1, False),
        ]

    def _get_community_menu_entries(self):
        self.ensure_one()
        return [('Community', '/event/%s/community' % slug(self), False, 80, 'community')]

    def _get_exhibitor_menu_entries(self):
        self.ensure_one()
        return [('Exhibitors', '/event/%s/exhibitors' % slug(self), False, 60, 'exhibitor')]
    
    def osm_iframe_by_pos(self):
        """ v14 ready """
        self.ensure_one()
        if self.address_id:
            return self.sudo().address_id.osm_iframe_by_pos()
        return None

    