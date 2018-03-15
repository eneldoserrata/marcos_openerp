# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
from openerp.osv import fields, osv
from openerp import netsvc

class sale_order(osv.Model):
    _inherit = "sale.order"

    def create_sales_order(self, cr, uid, orderline, customer_id, context=None):
        if context is None:
            context = {}
        sale_pool = self.pool.get('sale.order')
        prod_pool = self.pool.get('product.product')
        sale_line_pool = self.pool.get('sale.order.line')
        sale_no = ''
        sale = {}
        if customer_id:
            customer_id = int(customer_id)
            sale = ({'partner_id': customer_id, 'partner_invoice_id': customer_id, 'partner_shipping_id': customer_id})
            if context.get("shop_id", False):
                sale.update({'shop_id': context['shop_id']})
            part = sale_pool.onchange_partner_id(cr, uid, [], customer_id)['value']
            fiscal_position = part.get('fiscal_position')
            sale.update(part)
            sale_id = sale_pool.create(cr, uid, sale)
            sale_no = sale_pool.browse(cr, uid, sale_id).name
            #create sale order line
            sale_line = {'order_id': sale_id}
            for line in orderline:
                prod_rec = prod_pool.browse(cr, uid, line['product_id'])
                sale_line.update({'name': prod_rec.name or False,
                                  'product_id': prod_rec.id,
                                  'product_uom_qty':line['qty']})
                prod = sale_line_pool.product_id_change(cr, uid, [], sale['pricelist_id'],
                                                        prod_rec.id, qty=line['qty'], partner_id=customer_id,
                                                        fiscal_position=fiscal_position)['value']
                prod.update({'price_unit': line.get('price_unit', 0)})

                sale_line.update(prod)
                taxes = map(lambda a: a.id, prod_rec.taxes_id)
                if sale_line.get('tax_id'):
                    sale_line.update({'tax_id': [(6, 0, sale_line.get('tax_id'))]})
                else:
                    sale_line.update({'tax_id': [(6, 0, taxes)]})
                sale_line_pool.create(cr, uid, sale_line)
        return {"sale_id": sale_id, "sale_no": sale_no}

    def get_quotation_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context["active_ids"] = ids
        datas = {'ids': ids or [],
                 'model': 'sale.order',
                 'form': self.read(cr, uid, ids, context=context)[0]
                }
        return {'type': 'ir.actions.report.xml',
                'report_name': 'sale.order',
                'datas': datas,
                'context': context
                }


class account_fiscal_position(osv.Model):
    _inherit = 'account.fiscal.position'
    
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = set()
        if taxes and isinstance(taxes[0], int):
            fobj = self.browse(cr, uid, fposition_id)
            tax_obj = self.pool.get('account.fiscal.position.tax')
            
            for t in tax_obj.browse(cr, uid, taxes):
                ok = False
                for tax in fobj.tax_ids:
                    if tax.tax_src_id.id == t.id:
                        if tax.tax_dest_id:
                            result.add(tax.tax_dest_id.id)
                        ok=True
                if not ok:
                    result.add(t.id)
        else:
            if not taxes:
                return []
            if not fposition_id:
                return map(lambda x: x.id, taxes)
            for t in taxes:
                ok = False
                for tax in fposition_id.tax_ids:
                    if tax.tax_src_id.id == t.id:
                        if tax.tax_dest_id:
                            result.add(tax.tax_dest_id.id)
                        ok=True
                if not ok:
                    result.add(t.id)
        return list(result)