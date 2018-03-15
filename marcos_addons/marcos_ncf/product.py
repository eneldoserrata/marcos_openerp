# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class product_category(osv.osv):
    _inherit = "product.category"

    def on_change_parent_id(self, cr, uid, ids, parent_id, context=None):
        parent_category = self.browse(cr, uid, parent_id)
        if parent_category.property_stock_account_input_categ:
            property_stock_account_input_categ = parent_category.property_stock_account_input_categ.id
            property_stock_account_output_categ = parent_category.property_stock_account_output_categ.id
            property_stock_valuation_account_id = parent_category.property_stock_valuation_account_id.id

            return {"value": {'property_stock_account_input_categ': property_stock_account_input_categ,
                              'property_stock_account_output_categ': property_stock_account_output_categ,
                              'property_stock_valuation_account_id': property_stock_valuation_account_id}}
        return {"value": {}}
