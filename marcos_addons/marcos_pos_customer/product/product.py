# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

class product_product(osv.Model):
    _inherit = "product.product"
    _columns = {
        'serial_required': fields.boolean(
            u'Número de serie requerido en POS',
            help=u"Nº de serie se requiere en el punto de venta."),
        'color': fields.char("Color")
    }
