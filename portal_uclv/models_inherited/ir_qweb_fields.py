from odoo.http import request
from odoo import models, fields


class Contact(models.AbstractModel):
    _inherit = 'ir.qweb.field.contact'

