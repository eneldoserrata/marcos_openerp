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
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}

        if context.get('qty_exists') == True:
            pids = self.search(cr, uid, [])
            if pids:
                prod = self.browse(cr, uid, pids)
                pp = map(lambda a: a.id, filter(lambda a: a.qty_available > 0, prod))
                args += [('id', 'in', pp)]
        if context and context.get('search_default_categ_id', False):
            args.append((('categ_id', 'child_of', context['search_default_categ_id'])))
        return super(product_product, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)
