# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
from openerp.osv import osv
from openerp.tools.translate import _


# Fix bug update location_id when onchange_warehouse_id
class purchase_order(osv.Model):
    _inherit = "purchase.order"

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        if not warehouse_id:
            return {}
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        self.write(cr, uid, ids, {'location_id': warehouse.lot_input_id.id}) # eneldo add this line
        return {'value': {'location_id': warehouse.lot_input_id.id, 'dest_address_id': False}}

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                }}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        supplier = partner.browse(cr, uid, partner_id)
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
            'payment_term_id': supplier.property_supplier_payment_term.id or False,
            'invoice_method': supplier.invoice_method or 'order'
            }}

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        currency_obj = self.pool.get('res.currency')
        for po in self.browse(cr, uid, ids, context=context):
            currency_id = po.pricelist_id.currency_id.id
            company_currency = self.pool.get('res.company').browse(cr, uid, po.company_id.id).currency_id.id
            if not po.order_line:
                raise osv.except_osv(_('Error!'), _('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state == 'draft':
                    group_costing_method = False
                    purchase_settings_ids = self.pool.get('purchase.config.settings').search(cr, uid, [], order='id desc')
                    if purchase_settings_ids:
                        group_costing_method = self.pool.get('purchase.config.settings').\
                            read(cr, uid, purchase_settings_ids[0], ['group_costing_method'])['group_costing_method']

                    # Update standard price for product based on purchase price.
                    # Considering: Purchase UOM, Currency Rate,
                    # and group_costing_method is not active.
                    if not group_costing_method:
                        price = currency_obj.compute(cr, uid, currency_id, company_currency, line.price_unit)
                        standard_price = price * line.product_uom.factor
                        self.pool.get('product.product').write(cr, uid, [line.product_id.id], {'standard_price': standard_price})
                    todo.append(line.id)

        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        line_obj = self.pool.get("purchase.order.line")
        for id in ids:
            line_ids = line_obj.search(cr, uid, [("order_id", "=", id)])
            line_obj.write(cr, uid, line_ids, {"state": "draft"})
        return super(purchase_order, self).action_cancel_draft(cr, uid, ids, context=None)
        # if not len(ids):
        #     return False
        # self.write(cr, uid, ids, {'state':'draft','shipped':0})
        # wf_service = netsvc.LocalService("workflow")
        # for p_id in ids:
        #     # Deleting the existing instance of workflow for PO
        #     wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
        #     wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        # return True
