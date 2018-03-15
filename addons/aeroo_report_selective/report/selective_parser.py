# -*- coding: utf-8 -*-

from openerp.report import report_sxw
from openerp import pooler
import logging

class SelectiveCategory(object):
    """
    Represents a single category in a report.
    """

    def __init__(self, sequence, name, code, lines = []):
        self.sequence = sequence
        self.name = name
        self.code = code
        self.lines = lines

        # Computes category total and discount
        cat_total = 0.0
        total_discount = 0.0
        
        for line in self.lines:
            cat_total += line.price_subtotal
            total_discount += (line.discount * (line.price_unit * line.product_uom_qty) / 100)
        
        self.discount = total_discount
        self.total = cat_total

    def __repr__(self):
        return self.name        

class Parser(report_sxw.rml_parse):
    """
    Used to group products by their template categories.
    """

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.cr = cr
        self.uid = uid
        self.pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
            'get_by_categories': self._get_by_categories
        })
        self.context = context

    def _get_by_categories(self, resource_type, id):
        """
        Gets product lines ordered by categories depending on type of resource (invoice/order).
        """
        context = {}
        res = []
        categories = {}

        try:
            res_obj = self.pool.get(resource_type)
            resource = res_obj.browse(self.cr, self.uid, id, context = context)
        except:
            logging.error('OpenERP type %s not found!' % resource_type)
            return res

        # Retrieve aeroo templates
        aeroo_tpl_obj = self.pool.get('aeroo.product.template')
        aeroo_tpls = aeroo_tpl_obj.browse(self.cr, self.uid, 
            aeroo_tpl_obj.search(self.cr, self.uid, [], context = context), context = context)

        # Convert to dict id: browse_record
        tpls = dict([(x.id, x) for x in aeroo_tpls])

        if(resource_type == 'account.invoice'):
            lines = resource.invoice_line
        elif(resource_type == 'sale.order'):
            lines = resource.order_line
        else:
            logging.error('Type %s not supported for now!' % resource_type)
            return res

        for line in lines:
            if line.product_id:
                product_type = line.product_id.aeroo_template_id and line.product_id.aeroo_template_id.id or False
                if product_type:
                    categories.setdefault(product_type, []).append(line)
                else:
                    categories.setdefault('none', []).append(line)

        # Create appropriate object for each category
        for tpl_id in categories.keys():
            if tpl_id == 'none':
                res.append(SelectiveCategory(
                    1000,
                    'none',
                    'none',
                    categories[tpl_id]))
            else:
                res.append(SelectiveCategory(
                    tpls[tpl_id].sequence,
                    tpls[tpl_id].name,
                    tpls[tpl_id].code,
                    categories[tpl_id]))

        # Sort by sequence
        res.sort(key = lambda c: c.sequence)

        print res

        return res