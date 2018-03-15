# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from idvalidator import is_identification
from openerp.osv.fields import _column
from openerp.osv.orm import browse_null
from openerp.tools.translate import _
from openerp import netsvc, tools
import time
from openerp.osv.orm import browse_record


class inherit_pos_config(osv.Model):
    _name = "pos.config"
    _inherit = "pos.config"

    _columns = {
        "iface_printer_host": fields.char("Host para impresora fiscal"),
        "iface_printer_model": fields.char("Modelo de impresora fiscal")
    }


class inherit_res_partner(osv.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    def _check_unique_ref(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids, context=context)[0]
        if partner.customer:
            if partner.is_company and not partner.ref:
                return False
            elif partner.is_company and isinstance(partner.property_account_position, browse_null):
                return False
            elif partner.is_company and is_identification(partner.ref):
                return True
            elif partner.is_company is False:
                return True
        else:
            return True

    _constraints = [
        (osv.osv._check_recursion, 'You cannot create recursive Partner hierarchies.', ['parent_id']),
        (_check_unique_ref, u"Los datos fiscales no son valido revise RNC/Cédula y la posición fiscal", [u"Rnc/Cédula"]),
    ]


class inherit_sale_shop(osv.Model):
    _name = 'sale.shop'
    _inherit = 'sale.shop'

    _columns = {
        'fiscal_id': fields.many2one('account.journal', u'NCF Con valor fiscal', help=u"Facturas que Generan Crédito y Sustentan Costos y/o Gastos.", required=True),
        'final_id': fields.many2one('account.journal', u'NCF Consumidor final', help=u"Facturas para Consumidores Finales.", required=True),
        'especiales_id': fields.many2one('account.journal', u'NCF Regímenes Especiales', help=u"Regímenes Especiales de Tributación.", required=True),
        'gubernamentales_id': fields.many2one('account.journal', u'NCF Gubernamentales', help=u"Comprobantes Gubernamentales.", required=True),
        'notas_credito_id': fields.many2one('account.journal', u'NCF Notas de credito', help=u"Comprobantes Notas de credito.", required=True),
        'default_partner_id': fields.many2one('res.partner', u'Cliente de contado', help=u"Se asignara este cliente por defecto cuando "
                                                                                      u"cuando se grabe la factura sin un cliente seleccionado.", required=True)
    }


class inherit_account_fiscal_position(osv.Model):
    _name = 'account.fiscal.position'
    _inherit = 'account.fiscal.position'

    def _get_fiscal_type(self, cursor, user_id, context=None):
        return (
            ("final", u"Facturas para Consumidores Finales"),
            ("fiscal", u"Facturas que Generan Crédito y Sustentan Costos y/o Gastos"),
            ("final_note", u"Nota de crédito a consumidor final"),
            ("fiscal_note", u"Nota de crédito con derecho a crédito fiscal"),
            ("special", u"Regímenes Especiales de Tributación"),
            ("gov", u"Comprobantes Gubernamentales"),
            ("informal", u"Proveedores Informales"),
            ("minor", u"Gastos Menores"),
        )

    _columns = {
        "fiscal_type": fields.selection(_get_fiscal_type, "Tipo de NCF")
    }

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


class pos_order(osv.Model):
    _inherit = "pos.order"

    _columns = {
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('paid', 'Paid'),
                                   ('done', 'Posted'),
                                   ('invoiced', 'Invoiced'),
                                   ('ipf', 'Impreso')],
                                  'Status', readonly=True),
        'refund': fields.char('Refund', size=64, select=True, readonly=True)

    }

    _defaults = {'refund': lambda *a: False}

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
                'partner_id': order.get('partner_id')
            }, context)

            for payments in order['statement_ids']:
                payment = payments[2]
                self.add_payment(cr, uid, order_id, {
                    'amount': payment['amount'] or 0.0,
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
                    cash_journal_ids = filter(lambda st: st.journal_id.type == 'cash', session.statement_ids)
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
        order = self.pool.get('pos.order').browse(cr, uid, id, context=context)[0]
        partner_ref = order.partner_id.ref
        partner_name = order.partner_id.name

        shop = order.shop_id.id
        fiscal_type = order.partner_id.property_account_position.fiscal_type
        fiscal_position = order.partner_id.property_account_position.id or 2

        if fiscal_type == "gov" or fiscal_type == "special":
            fiscal_type = "fiscal"

        if not order.partner_id:
            raise osv.except_osv(_('Error!'), _('Debe de seleccionar un cliente!'))
        acc = order.partner_id.property_account_receivable.id
        invoice_type = "out_invoice"
        afecta = None
        if order.refund:
            invoice_type = "out_refund"
            afecta = context["afecta"] or None

        inv = {
            'name': order.name,
            'origin': order.name,
            'fiscal_position': fiscal_position,
            'account_id': acc,
            'journal_id': order.sale_journal.id or None,
            'type': invoice_type, #'out_invoice',
            'parent_id': afecta,
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
            if invoice_type == "out_refund":
                quantity = -line.qty
            else:
                quantity = line.qty
            inv_line = {
                'invoice_id': inv_id,
                'product_id': line.product_id.id,
                'quantity': quantity,
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
        wf_service.trg_validate(uid, 'pos.order', order.id, 'invoice', cr)
        wf_service.trg_validate(uid, 'account.invoice', inv_id, 'validate', cr)

        # Ejecuta el signal para generar la factura definitiva
        wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
        current_invoice = inv_ref.browse(cr, uid, inv_id)

        return [inv_id, current_invoice.number, partner_ref, fiscal_type, partner_name, shop, uid]

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

    def _get_journal_id(self, fiscal_type, shop_id, refund):

        if refund:
            return shop_id.notas_credito_id.id
        elif fiscal_type == "final" or fiscal_type is None:
            return shop_id.final_id.id
        elif fiscal_type == "fiscal":
            return shop_id.fiscal_id.id
        elif fiscal_type == "special":
            return shop_id.especiales_id.id
        elif fiscal_type == "gov":
            return shop_id.gubernamentales_id.id
        else:
            return False

    def create(self, cr, uid, values, context=None):
        if not values["lines"]:
            raise osv.except_osv( _('Error!'),
                                  _("No puede grabar un pedido sin productos"))

        session = self.pool.get("pos.session").browse(cr, uid, [values["session_id"]], context)[0]
        if not values["partner_id"]:
            values["partner_id"] = session.config_id.shop_id.default_partner_id.id

        partner = self.pool.get("res.partner").browse(cr, uid, [values["partner_id"]], context)[0]
        fiscal_type = partner.property_account_position.fiscal_type or "final"
        shop_id = session.config_id.shop_id
        refund = values.get("refund", False)

        new_order = super(pos_order, self).create(cr, uid, values, context=context)
        self.write(cr, uid, [new_order],
                   {"sale_journal": self._get_journal_id(fiscal_type, shop_id, refund), "refund": refund},
                   context=context)
        return new_order

    def refund(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        clone_list = []
        line_obj = self.pool.get('pos.order.line')

        for order in self.browse(cr, uid, ids, context=context):
            current_session_ids = self.pool.get('pos.session').search(cr, uid, [
                ('state', '!=', 'closed'),
                ('user_id', '=', uid)], context=context)
            if not current_session_ids:
                raise osv.except_osv(_('Error!'), _('To return product(s), you need to open a session that will be used to register the refund.'))

            name = None
            if order.amount_total >= 0:
                name = order.name

            clone_id = self.copy(cr, uid, order.id, {
                'name': name,
                'session_id': current_session_ids[0],
                'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
                'refund': name
            }, context=context)
            clone_list.append(clone_id)

        for clone in self.browse(cr, uid, clone_list, context=context):
            for order_line in clone.lines:
                line_obj.write(cr, uid, [order_line.id], {
                    'qty': -order_line.qty
                }, context=context)

        new_order = ','.join(map(str,clone_list))
        abs = {
            #'domain': "[('id', 'in', ["+new_order+"])]",
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id':clone_list[0],
            'view_id': False,
            'context':context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs

    def set_printed(self, cr, uid, oid, context=None):
        oid = self.write(cr, uid, oid, {"state":"ipf"}, context)
        return oid

    def print_on_ipf(self, cr, uid, name, context=None):
        context = context or {}
        inv_obj = self.pool.get("account.invoice")

        inv_id = inv_obj.search(cr, uid, [["origin", "=", name]])
        ord_id = self.search(cr, uid, [["name", "=", name]])

        inv = inv_obj.browse(cr, uid, inv_id, context)[0]
        ord = self.browse(cr, uid, ord_id, context)[0]
        cashier = self.perm_read(cr, uid, ord_id,  details=True)[0].get("write_uid", None)[1]

        fiscal_type = ord.partner_id.property_account_position.fiscal_type or "final"

        if fiscal_type == "gov" or fiscal_type == "special":
            fiscal_type = "fiscal"

        afecta = None
        if ord.refund:
            afecta = inv.parent_id.number
            if fiscal_type == "final":
                fiscal_type = "nota_final"
            else:
                fiscal_type = "nota_fiscal"

        data = {
            'branch': ord.shop_id.id,
            'brand': ord.session_id.config_id.iface_printer_model,
            'client': ord.partner_id.name,
            'fiscal_type': fiscal_type,
            'ncf': inv.number,
            "afecta": afecta,
            'oid[]': ord.id,
            'receipt[cashier]': cashier,
            'receipt[change]': ord.amount_return,
            #'receipt[client]': u'',
            # 'receipt[company][company_registry]': u'false',
            'receipt[company][contact_address]': ord.company_id.street+u" "+ord.company_id.street2+u" "+u" "+ord.company_id.city,
            'receipt[company][email]': ord.company_id.email,
            'receipt[company][name]': ord.company_id.name,
            'receipt[company][phone]': ord.company_id.phone,
            'receipt[company][vat]': ord.company_id.vat,
            'receipt[company][website]': ord.company_id.website,
            'receipt[currency][accuracy]': inv.currency_id.accuracy,
            'receipt[currency][id]': inv.currency_id.id,
            'receipt[currency][position]': inv.currency_id.position,
            'receipt[currency][rounding]': inv.currency_id.position,
            'receipt[currency][symbol]': inv.currency_id.symbol,
            'receipt[date][date]': inv.date_invoice,
            # 'receipt[date][day]': u'0',
            # 'receipt[date][hour]': u'10',
            # 'receipt[date][minute]': u'52',
            # 'receipt[date][month]': u'11',
            # 'receipt[date][year]': u'2013',
            'receipt[invoice_id]': inv.id,
            'receipt[name]': ord.pos_reference,

            # 'receipt[orderlines][0][discount]': u'0',
            # 'receipt[orderlines][0][price]': u'1',
            # 'receipt[orderlines][0][price_display]': u'1',
            # 'receipt[orderlines][0][price_with_tax]': u'1',
            # 'receipt[orderlines][0][price_without_tax]': u'1',
            # 'receipt[orderlines][0][product_description]': u'false',
            # 'receipt[orderlines][0][product_description_sale]': u'false',
            # 'receipt[orderlines][0][product_name]': u'Productos sin referencia',
            # 'receipt[orderlines][0][quantity]': u'1',
            # 'receipt[orderlines][0][tax]': u'0',
            # 'receipt[orderlines][0][unit_name]': u'Unidad(es)',

            # 'receipt[paymentlines][0][amount]': u'1',
            # 'receipt[paymentlines][0][journal]': u'Efectivo (DOP)',

            'receipt[shop][name]': ord.shop_id.name,
            'receipt[subtotal]': u'1',
            'receipt[total_discount]': u'0',
            'receipt[total_paid]': ord.amount_paid,
            'receipt[total_tax]': inv.amount_tax,
            'receipt[total_with_tax]': inv.amount_total,
            'receipt[total_without_tax]': inv.amount_untaxed,
            'rnc': ord.partner_id.ref,
            'uid': uid
        }
        import pprint
        pp = pprint.PrettyPrinter(indent=4)

        pp.pprint(data)





class pos_order_line(osv.Model):
    _inherit = "pos.order.line"
    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial No'),
    }


class product_product(osv.Model):
    _inherit = "product.product"
    _columns = {
        'serial_required': fields.boolean('Serial Number required in POS', help="Serial No. required in Point of Sale.")
    }


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
            sale = {'partner_id': customer_id, 'partner_invoice_id': customer_id, 'partner_shipping_id': customer_id}
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
                sale_line.update(prod)
                taxes = map(lambda a: a.id, prod_rec.taxes_id)
                if sale_line.get('tax_id'):
                    sale_line.update({'tax_id': [(6, 0, sale_line.get('tax_id'))]})
                else:
                    sale_line.update({'tax_id': [(6, 0, taxes)]})
                sale_line_pool.create(cr, uid, sale_line)
        return sale_no


class inherit_pos_session(osv.Model):
    _inherit = "pos.session"

    def _confirm_orders(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")

        for session in self.browse(cr, uid, ids, context=context):
            #order_ids = [order.id for order in session.order_ids if order.state == 'invoiced']

            #move_id = self.pool.get('account.move').create(cr, uid, {'ref' : session.name, 'journal_id' : session.config_id.journal_id.id, }, context=context)
            #self.pool.get('pos.order')._create_account_move_line(cr, uid, order_ids, session, move_id, context=context)

            for order in session.order_ids:
                if order.state not in ('paid', 'invoiced'):
                    raise osv.except_osv(
                        _('Error!'),
                        _("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                else:
                    invoice_ref = self.pool.get("account.invoice")
                    wf_service.trg_validate(uid, 'pos.order', order.id, 'done', cr)
                    invoice_ref.write(cr, uid, invoice_ref.search(cr, uid, [("reference", "=", order.name)]), {'state':'paid'}, context=context)

        return True

# class account_invoice(osv.Model):
#     _inherits = "account.invoice"

class inherit_pos_make_payment(osv.osv_memory):
    _inherit = 'pos.make.payment'
    _description = 'Point of Sale Payment'

    def check(self, cr, uid, ids, context=None):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        context = context or {}
        order_obj = self.pool.get('pos.order')

        obj_partner = self.pool.get('res.partner')
        active_id = context and context.get('active_id', False)

        order = order_obj.browse(cr, uid, active_id, context=context)
        amount = order.amount_total - order.amount_paid
        data = self.read(cr, uid, ids, context=context)[0]

        if order.refund:
            inv_obj= self.pool.get('account.invoice')
            refund_inv_ids = inv_obj.search(cr, uid, [("name", "=", order.refund)])
            context["afecta"] = refund_inv_ids[0]

        data['journal'] = data['journal_id'][0]

        if amount != 0.0:
            order_obj.add_payment(cr, uid, active_id, data, context=context)

        if order_obj.test_paid(cr, uid, [active_id]):
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'pos.order', active_id, 'paid', cr)

            #eneldo
            self.pool.get('pos.order').action_create_invoice(cr, uid, [order.id], context=context)

            return {'type': 'ir.actions.act_window_close'}
         ##self.print_report(cr, uid, ids, context=context)

        return self.launch_payment(cr, uid, ids, context=context)

import logging

_logger = logging.getLogger(__name__)

class publisher_warranty_contract(osv.Model):
    _inherit = 'publisher_warranty.contract'

    def update_notification(self, cr, uid, ids, cron_mode=True,
                            context=None):

        _logger.info("NO More Spying Stuff")

        return True


# Fix bug update location_id when onchange_warehouse_id
class purchase_order(osv.Model):
    _inherit = "purchase.order"

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        if not warehouse_id:
            return {}
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        self.write(cr, uid, ids, {'location_id': warehouse.lot_input_id.id}) # eneldo add this line
        return {'value':{'location_id': warehouse.lot_input_id.id, 'dest_address_id': False}}