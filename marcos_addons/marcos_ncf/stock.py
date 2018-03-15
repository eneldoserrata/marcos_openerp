# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    """
        Custom wizard create credit note when cancel pickin from supplier
    """

    def action_cancel(self, cr, uid, ids, context=None):
        """ Changes picking state to cancel.
        @return: True
        """
        order = self.read(cr, uid, ids, ['purchase_id'])[0]

        if order.get("purchase_id"):
            order = order['purchase_id'][0]

            invoice_method = self.pool.get('purchase.order').read(cr, uid, order, ['invoice_method'])['invoice_method']
            if invoice_method == u'order':
                self.write(cr, uid, ids, {'invoice_state': '2binvoiced'}, context=context)
                view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'marcos_ncf', 'marcos_view_stock_invoice_onshipping')[1]

                wizard = {
                    'name': 'Generar nota de credito',
                    'view_mode': 'form',
                    'view_id': False,
                    'views': [(view_id, 'form')],
                    'view_type': 'form',
                    'res_model': 'marcos.stock.invoice.onshipping',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
                return wizard
            for pick in self.browse(cr, uid, ids, context=context):
                ids2 = [move.id for move in pick.move_lines]
                self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
            self.write(cr, uid, ids, {'state': 'cancel', 'invoice_state': 'none'})
            return True
        else:
            return super(stock_picking, self).action_cancel(cr, uid, ids, context=context)



class stock_move(osv.osv):
    _inherit = "stock.move"

    def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
        """
        Return the reference amount and reference currency representing the inventory valuation for this move.
        These reference values should possibly be converted before being posted in Journals to adapt to the primary
        and secondary currencies of the relevant accounts.
        """
        product_uom_obj = self.pool.get('product.uom')

        # by default the reference currency is that of the move's company
        reference_currency_id = move.company_id.currency_id.id

        default_uom = move.product_id.uom_id.id
        qty = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)

        # taxes list for product piking
        taxes = move.product_id.supplier_taxes_id

        # if product is set to average price and a specific value was entered in the picking wizard,
        # we use it
        if move.product_id.cost_method == 'average' and move.price_unit:
            reference_amount = qty * move.price_unit

            # check if tax is price include
            if taxes:
                reference_amount = self._tax_remove(taxes, reference_amount)

            reference_currency_id = move.price_currency_id.id or reference_currency_id

        # Otherwise we default to the company's valuation price type, considering that the values of the
        # valuation field are expressed in the default currency of the move's company.
        else:
            if context is None:
                context = {}
            currency_ctx = dict(context, currency_id = move.company_id.currency_id.id)
            amount_unit = move.product_id.price_get('standard_price', context=currency_ctx)[move.product_id.id]
            reference_amount = amount_unit * qty
            if taxes:
                reference_amount = self._tax_remove(taxes, reference_amount)
        return reference_amount, reference_currency_id

    def _tax_remove(self, taxes, reference_amount):
        for tax in taxes:
            if tax.price_include:
                tax_amount = tax.amount+1
                reference_amount = reference_amount/tax_amount
        return reference_amount

    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        if move.product_id.valuation == 'real_time': # FIXME: product valuation should perhaps be a property?
            if context is None:
                context = {}
            src_company_ctx = dict(context,force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context,force_company=move.location_dest_id.company_id.id)
            account_moves = []
            # Outgoing moves (or cross-company output part)
            if move.location_id.company_id \
                and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #returning goods to supplier
                if move.location_dest_id.usage == 'supplier':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_src, reference_amount, reference_currency_id, context))]
                else:
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

            # Incoming moves (or cross-company input part)
            if move.location_dest_id.company_id \
                and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #goods return from customer
                if move.location_id.usage == 'customer':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_dest, acc_valuation, reference_amount, reference_currency_id, context))]
                else:
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')
            period_obj = self.pool.get('account.period')
            if context.get("late_move", False):
                for j_id, move_lines in account_moves:
                    move_obj.create(cr, uid,
                            {
                             'journal_id': j_id,
                             'line_id': move_lines,
                             'ref': move.picking_id and move.picking_id.name,
                             'date': move.picking_id.date_done,
                             'period_id': period_obj.find(cr, uid, move.picking_id.date_done)[0]
                            }, context=context)
            else:
                for j_id, move_lines in account_moves:
                    move_obj.create(cr, uid,
                            {
                             'journal_id': j_id,
                             'line_id': move_lines,
                             'ref': move.picking_id and move.picking_id.name,
                            }, context=context)