# -*- coding: utf-8 -*-

from openerp.osv import orm, fields

class aeroo_product_template(orm.Model):

    _name = "aeroo.product.template"

    _columns = {
        "name": fields.char("Name", help = "Name of the template", size = 255, required = True),
        "code": fields.char("Code", help = "Code used in the report file", size = 50, required = True),
        "sequence": fields.integer("Sequence", help = "Order in which it should appear", required = True)
    }

    _defaults = {
        "sequence": 10
    }