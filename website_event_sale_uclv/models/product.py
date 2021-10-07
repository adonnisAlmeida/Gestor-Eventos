# -*- coding: utf-8 -*-

from odoo import fields, models


# defined for access rules
class Product(models.Model):
    _inherit = 'product.product'
    event_ticket_ids = fields.One2many('event.event.ticket', 'product_id', string='Event Tickets')

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def get_rule(self, product, quantity, partner, date=False, uom_id=False):
        """ For a given pricelist, return rule for a given product """
        self.ensure_one()
        rule_id = self._compute_price_rule([(product, quantity, partner)], date=date, uom_id=uom_id)[product.id][1]
        if rule_id:
            return self.env['product.pricelist.item'].browse(rule_id)
        return False

    