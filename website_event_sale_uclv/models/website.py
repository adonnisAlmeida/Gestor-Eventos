# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def get_countries(self):
        return self.env['res.country'].sudo().search([])

    def get_geoip_code(self):
        website = request and hasattr(request, 'website') and request.website or None
        
        return request.httprequest.headers
        
        
        if not website:
            if self.env.context.get('website_id'):
                website = self.browse(self.env.context['website_id'])
            else:
                # In the weird case we are coming from the backend (https://github.com/odoo/odoo/issues/20245)
                website = len(self) == 1 and self or self.search([], limit=1)
        
        return request and request.session.geoip and request.session.geoip.get('country_code') or False

    def get_pricelist_available(self, show_visible=False):

        """ Return the list of pricelists that can be used on website for the current user.
        Country restrictions will be detected with GeoIP (if installed).
        :param bool show_visible: if True, we don't display pricelist where selectable is False (Eg: Code promo)
        :returns: pricelist recordset
        """
        website = request and hasattr(request, 'website') and request.website or None
        if not website:
            if self.env.context.get('website_id'):
                website = self.browse(self.env.context['website_id'])
            else:
                # In the weird case we are coming from the backend (https://github.com/odoo/odoo/issues/20245)
                website = len(self) == 1 and self or self.search([], limit=1)
        isocountry = request and request.session.geoip and request.session.geoip.get('country_code') or False
        partner = self.env.user.partner_id
        order_pl = partner.last_website_so_id and partner.last_website_so_id.state == 'draft' and partner.last_website_so_id.pricelist_id
        partner_pl = partner.property_product_pricelist
        pricelists = website._get_pl_partner_order(isocountry, show_visible,
                                                   website.user_id.sudo().partner_id.property_product_pricelist.id,
                                                   request and request.session.get('website_sale_current_pl') or None,
                                                   website.pricelist_ids,
                                                   partner_pl=partner_pl and partner_pl.id or None,
                                                   order_pl=order_pl and order_pl.id or None)
        return self.env['product.pricelist'].browse(pricelists)

    def sale_product_domain(self):
        # remove product event from the website content grid and list view (not removed in detail view)
        return ['&'] + super(Website, self).sale_product_domain() + [('event_ok', '=', False)]
