# -*- coding: utf-8 -*-

from openerp.osv import orm, fields

class product_product(orm.Model):

    _inherit = 'product.product'

    _columns = {
        "aeroo_template_id": fields.many2one("aeroo.product.template", "Aeroo report category")
    }