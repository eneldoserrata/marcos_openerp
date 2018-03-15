# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc, tools
import time


class pos_order(osv.Model):
    _inherit = "pos.order"
    _columns = {
        'parent_return_order': fields.char('Return Order ID', size=64),
        'return_seq': fields.float('Return Sequence')
    }

    def create_from_ui(self, cr, uid, orders, context=None):
        order_ids = []
        lot_obj = self.pool.get('stock.production.lot')
        for tmp_order in orders:
            order = tmp_order['data']
            if order.get('lines'):
                for line in order['lines']:
                    l = line[2]
                    if l.get('prodlot_id'):
                        lot = {'name': l['prodlot_id'],
                               'product_id': l['product_id']}
                        lot_id = lot_obj.create(cr, uid, lot)
                        l.update({'prodlot_id': lot_id})
                        line[2] = l
            order_id = self.create(cr, uid, {
                'name': order['name'],
                'user_id': order['user_id'] or False,
                'session_id': order['pos_session_id'],
                'lines': order['lines'],
                'pos_reference':order['name'],
                'partner_id': order.get('partner_id'),
                'parent_return_order': order.get('parent_return_order', ''),
                'return_seq': order.get('return_seq', 0),
                'note': order.get('note')
            }, context)

            for payments in order['statement_ids']:
                payment = payments[2]
                if order.get('parent_return_order', ''):
                    amount = -payment['amount'] or 0.0
                else:
                    amount = payment['amount'] or 0.0
                self.add_payment(cr, uid, order_id, {
                    'amount': amount,
                    'payment_date': payment['name'],
                    'statement_id': payment['statement_id'],
                    'payment_name': payment.get('note', False),
                    'journal': payment['journal_id']
                }, context=context)

            if order['amount_return']:
                session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)
                cash_journal = session.cash_journal_id
                cash_statement = False
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type=='cash', session.statement_ids)
                    if not len(cash_journal_ids):
                        raise osv.except_osv( _('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                self.add_payment(cr, uid, order_id, {
                    'amount': -order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                }, context=context)
            order_ids.append(order_id)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'pos.order', order_id, 'paid', cr)
        return order_ids
    
    def action_create_invoice(self, cr, uid, id, context=None):
        wf_service = netsvc.LocalService("workflow")
        inv_ref = self.pool.get('account.invoice')
        inv_line_ref = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        inv_id = False
        order = self.pool.get('pos.order').browse(cr, uid, id, context=context)
        order = order[0]
        if not order.partner_id:
            raise osv.except_osv(_('Error!'), _('Please select customer !'))
        acc = order.partner_id.property_account_receivable.id
        inv = {
            'name': order.name,
            'origin': order.name,
            'account_id': acc,
            'journal_id': order.sale_journal.id or None,
            'type': 'out_invoice',
            'reference': order.name,
            'partner_id': order.partner_id.id,
            'comment': order.note or '',
            'currency_id': order.pricelist_id.currency_id.id, # considering partner's sale pricelist's currency
        }
        inv.update(inv_ref.onchange_partner_id(cr, uid, [], 'out_invoice', order.partner_id.id)['value'])
        if not inv.get('account_id', None):
            inv['account_id'] = acc
        inv_id = inv_ref.create(cr, uid, inv, context=context)
        self.write(cr, uid, [order.id], {'invoice_id': inv_id, 'state': 'invoiced'}, context=context)
        for line in order.lines:
            inv_line = {
                'invoice_id': inv_id,
                'product_id': line.product_id.id,
                'quantity': line.qty,
            }
            inv_name = product_obj.name_get(cr, uid, [line.product_id.id], context=context)[0][1]
            inv_line.update(inv_line_ref.product_id_change(cr, uid, [],
                                                           line.product_id.id,
                                                           line.product_id.uom_id.id,
                                                           line.qty, partner_id = order.partner_id.id,
                                                           fposition_id=order.partner_id.property_account_position.id)['value'])
            if line.product_id.description_sale:
                inv_line['note'] = line.product_id.description_sale

            inv_line['price_unit'] = line.price_unit
            inv_line['discount'] = line.discount
            inv_line['name'] = inv_name
            inv_line['invoice_line_tax_id'] = [(6, 0, [x.id for x in line.product_id.taxes_id] )]
            inv_line_ref.create(cr, uid, inv_line, context=context)

        inv_ref.button_reset_taxes(cr, uid, [inv_id], context=context)
        wf_service.trg_validate(uid, 'account.invoice', inv_id, 'validate', cr)
        return inv_id
    
    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):
            if not order.state=='draft':
                continue
            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            picking_id = picking_obj.create(cr, uid, {
                'origin': order.name,
                'partner_id': addr.get('delivery',False),
                'type': 'out',
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'note': order.note or "",
                'invoice_state': 'none',
                'auto_picking': True,
            }, context=context)

            self.write(cr, uid, [order.id], {'picking_id': picking_id}, context=context)

            location_id = order.shop_id.warehouse_id.lot_stock_id.id

            output_id = order.shop_id.warehouse_id.lot_output_id.id

            for line in order.lines:
                if line.product_id and line.product_id.type == 'service':
                    continue
                if line.qty < 0:
                    location_id, output_id = output_id, location_id

                move_obj.create(cr, uid, {
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uos': line.product_id.uom_id.id,
                    'picking_id': picking_id,
                    'product_id': line.product_id.id,
                    'product_uos_qty': abs(line.qty),
                    'product_qty': abs(line.qty),
                    'tracking_id': False,
                    'state': 'draft',
                    'location_id': location_id,
                    'location_dest_id': output_id,
                    'prodlot_id': line.prodlot_id and line.prodlot_id.id or False,
                }, context=context)
                if line.qty < 0:
                    location_id, output_id = output_id, location_id

            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            picking_obj.force_assign(cr, uid, [picking_id], context)
        return True

    def get_refund_data(self, cr, uid, ids, context=None):
        """
        'id', 'pos_reference', 'partner_id', property_account_position, fiscal_type
        """
        pass

    def get_partner_temp_name(self, cr, uid, id, context=None):
        result = self.read(cr, uid, id, ['temp_name', 'name', 'partner_id'])
        temp_name = result['temp_name'] or result['partner_id'][1]
        return {"order": result['name'], "temp_name": temp_name}

    def get_property_account_position_fiscal_type(self, cr, uid, partner_id, order_id, context=None):
        pos_order_line_obj = self.pool.get("pos.order.line")
        partner = self.pool.get("res.partner").browse(cr, uid, partner_id)
        order_lines_ids = pos_order_line_obj.search(cr, uid, [('order_id', '=', order_id), ('return_qty', '>', 0)])
        order_lines = pos_order_line_obj.read(cr, uid, order_lines_ids)
        tax_id = False
        if partner.property_account_position.fiscal_type == "special":
            tax_id = partner.property_account_position.tax_ids[0].tax_dest_id.id
        return tax_id, order_lines

class pos_order_line(osv.Model):
    _inherit = "pos.order.line"
    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial No'),
        'return_qty': fields.float('Return QTY')
    }

