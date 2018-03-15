# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
from idvalidator import is_ncf
from openerp.osv.osv import except_osv
from openerp import netsvc

from datetime import datetime
from openerp.tools.translate import _
import time

class account_invoice(osv.Model):
    _inherit = "account.invoice"
    _name = "account.invoice"

    def _get_reference_type(self, cr, uid, context=None):
        return [('none', u'Referencia libre / Nº Fact. Proveedor'),
                ('01', '01 - Gastos de personal'),
                ('02', '02 - Gastos por trabajo, suministros y servicios'),
                ('03', '03 - Arrendamientos'),
                ('04', '04 - Gastos de Activos Fijos'),
                ('05', u'05 - Gastos de Representación'),
                ('06', '06 - Otras Deducciones Admitidas'),
                ('07', '07 - Gastos Financieros'),
                ('08', '08 - Gastos Extraordinarios'),
                ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
                ('10', '10 - Adquisiciones de Activos'),
                ('11', '11 - Gastos de Seguro')
        ]

    def on_change_fiscal_position(self, cr, uid, ids, value):
        fiscal_type = self.pool.get("account.fiscal.position").browse(cr, uid, value).fiscal_type
        if fiscal_type in [u'informal', u'minor']:
            ncf_required = False
        else:
            ncf_required = True
        return {"value": {'reference_type': fiscal_type, 'ncf_required': ncf_required}}

    def onchange_journal_id(self, cr, uid, ids, *args):
        if args:
            journal = self.pool.get("account.journal").browse(cr, uid, args[0])
            ncf_required = True
            if journal.ncf_special:
                ncf_required = False
            return {"value": {'ncf_required': ncf_required}}
        else:
            return {"value": {}}

    def onchange_reference(self, cr, uid, ids, reference, ncf_required):
        if not is_ncf(reference.encode("ascii")) and ncf_required:
            raise except_osv(u"NCF Invalido!", u"El NCF del proveedor no es válido!")
        return False

    def action_date_assign(self, cr, uid, ids, *args):
        for inv in self.browse(cr, uid, ids):
            if inv.journal_id.ncf_special in ['gasto', 'informal']:
                    self.write(cr, uid, [inv.id], {"reference": False})
            if inv.type in ['in_invoice', 'in_refund'] and inv.ncf_required:
                if inv.reference_type != 'none' and not is_ncf(inv.reference.encode("ascii")):
                    raise except_osv(u"NCF Invalido!", u"El NCF del proveedor no es válido!")
                    # TODO si la entrada de almacen referente a este pedido advertir al contador que debe terminar de recibir
                    # los productos pendientes o cancelarlos en caso de que se reciba parciarmente debe crear una nota de credito
                    # borrador

            res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice)
            if res and res['value']:
                self.write(cr, uid, [inv.id], res['value'])
        return True

    _columns = {
        'reference_type': fields.selection(_get_reference_type, 'Payment Reference',
                                           required=True, readonly=False),
        'reference': fields.char('Invoice Reference', size=19, help="The partner reference of this invoice."),
        'ipf': fields.boolean("Impreso", readonly=True),
        'ncf_required': fields.boolean(),
        "pay_to": fields.many2one("res.partner", "Pagar a")
    }

    _sql_constraints = [
        # ('number_uniq', 'unique(number, company_id, journal_id, type)', 'Invoice Number must be unique per Company!')
        ('number_uniq', 'unique(company_id, partner_id, number, journal_id)', u'El NCF para este relacionado ya fue utilizado!'),
    ]

    _defaults = {
        "ncf_required": True
    }

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

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}

        if context.get('active_model', False) == 'pos.order' and vals.get('type', False) in ["out_invoice", 'out_refund']:
            pass
        elif context.get('active_model', False) == 'stock.picking.in' and vals.get('type', False) == "out_refund":
            pass
        elif vals.get('type', False) == "out_invoice":
            order_obj = self.pool.get('sale.order')
            so_id = order_obj.search(cr, uid, [('name', '=', vals['origin'])])
            so = order_obj.browse(cr, uid, so_id, context)[0]
            if not vals['fiscal_position']: vals['fiscal_position'] = 2
            fiscal_type = so.partner_id.property_account_position.fiscal_type or 'final'
            vals['journal_id'] = self._get_journal_id(fiscal_type, so.shop_id, False)
        elif vals.get('type', False) == "out_refund":
            if vals.get('origin', False):
                order_obj = self.pool.get('sale.order')
                so_id = order_obj.search(cr, uid, [('name', '=', vals.get('origin', None))])
                so = order_obj.browse(cr, uid, so_id, context)[0]
                if not vals['fiscal_position']:
                    vals['fiscal_position'] = 2
                vals['journal_id'] = self._get_journal_id(None, so.shop_id, True)
            else:
                vals['reference'] = u""
                inv_obj = self.pool.get('account.invoice')
                origin = inv_obj.read(cr, uid, context['active_id'], ['number'])
                vals['origin'] = origin["number"]
        elif vals.get('type', False) == "in_invoice" and vals.get('fiscal_position', False):
            fiscal_type = self.pool.get("account.fiscal.position").browse(cr, uid, vals['fiscal_position']).fiscal_type
            vals['reference_type'] = fiscal_type
        elif vals.get('type', False) == "in_refund" and vals.get('fiscal_position', False):
            vals['reference'] = vals.get('origin', "")
            fiscal_type = self.pool.get("account.fiscal.position").browse(cr, uid, vals['fiscal_position']).fiscal_type
            vals['reference_type'] = fiscal_type

        inv = super(account_invoice, self).create(cr, uid, vals, context)
        return inv

        # go from canceled state to draft state

    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft', 'internal_number': False})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_delete(uid, 'account.invoice', inv_id, cr)
            wf_service.trg_create(uid, 'account.invoice', inv_id, cr)
        return True
    
    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        """
        For each invoice line.
            If amount of days since invoice is greater than 30.
                For each tax on each invoice line.
                If the tax is included in the price.
                The tax is replaced with the corresponding tax exempt tax.
                If tax is not include in price, no tax will show up in the refund.

        """

        result = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines, context=context)

        # For each invoice_line
        for x, y, line in result:
            inv_obj = self.pool.get('account.invoice').browse(cr, uid, line['invoice_id'], context=context)
            inv_date = datetime.strptime(inv_obj['date_invoice'], "%Y-%m-%d").date()
            days_diff = datetime.today().date() - inv_date
            # If amount of days since invoice is greater than 30:
            if days_diff.days > 30:
                taxes_ids = []
                # For each tax on the invoice line:
                for tax_id in line['invoice_line_tax_id'][0][2]:
                    tax_original = self.pool.get('account.tax').browse(cr, uid, tax_id, context=context)
                    # If the tax is included in the price:
                    if tax_original.price_include:
                        # Replace it with the corresponding tax exempt tax.
                        tax_replacement = self.pool.get('account.tax').search(cr, uid,
                                                                              [('type_tax_use', '=', tax_original.type_tax_use),
                                                                               ('amount', '=', tax_original.amount),
                                                                               ('exempt', '=', True),
                                                                               ],
                                                                              context=context)[0]
                        # No duplicate taxes allowed
                        if tax_replacement not in taxes_ids:
                            taxes_ids.append(tax_replacement)
                # If tax is not include in price, no tax will show up in the refund.
                line['invoice_line_tax_id'] = [(6, 0, taxes_ids)]

        return result

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        if invoice_browse.pay_to:
            supplier_account_id = invoice_browse.partner_id.property_account_payable.id
            for line in [lines[2] for lines in move_lines]:
                if line.get("account_id", False) == supplier_account_id:
                    line.update({'partner_id': invoice_browse.pay_to.id, 'account_id': invoice_browse.pay_to.property_account_payable.id})
        return move_lines
