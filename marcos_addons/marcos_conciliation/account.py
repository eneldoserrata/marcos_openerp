# -*- coding: utf-8 -*-

from openerp.osv import osv, fields


class account_journal(osv.Model):
    _inherit = 'account.journal'

    def _get_dst_journal(self, cr, uid, context=None):
        journal_obj = self.pool.get("account.journal")
        journal_ids =  journal_obj.search(cr, uid, [("type", "=", "bank"), ("journal_user", "=", False), ("allow_check_writing", "=", False)], context=context)
        journal_list = journal_obj.read(cr, uid, journal_ids, ["name"], context=context)
        return [(r['id'], r['name']) for r in journal_list]

    _columns = {
        'have_partner': fields.boolean(u'Requiere un relacionado'),
        'account_transit': fields.many2one('account.account', u'Cuenta de transito',
                                           help=u"Cuenta usada para hacer transferencias de dinero entre bancos y libros de caja"),
        "electronic_payment": fields.boolean(u"Pago electronico con cargos", help=u"Utilice esta opcion para cobros con veryphone o medios electronicos que generan cargos"),
        "save_charge_account_id": fields.many2one('account.account', u'Cuenta del cargo', domain="[('type','=','other')]",
                                                  help=u"Debe de ser una cuenta de activo que guardara los cargos para"
                                                       u"luego aplicar el pago a las facturas generadas por la entidad"
                                                       u"financiera"),
        "save_charge_percent": fields.float(u"% Del Recargo"),
        "tax_retention_account_id": fields.many2one('account.account', u'Cuenta de retención de impuesto', domain="[('type','=','other')]",
                                                  help=u"Debe de ser una cuenta de activo que guardara las retenciones"
                                                       u"de impuestos para luego aplicar a al pago de la norma"),
        "tax_retention_percent": fields.float(u"% Del Impuesto retenido"),
        'dst_bank_id': fields.many2one("res.partner.bank", "Banco de destino"),
        'tax_code_id': fields.many2one('account.tax.code', 'Codigo del impuesto', help="Use this code for the tax declaration."),
        # 'dst_journal_id': fields.selection(_get_dst_journal, "Diario del banco de destino")

        # 'dst_journal_id': fields.selection(_get_dst_journal, 'Diario Del Banco'),
    }

    _defaults = {
        'have_partner': False,
    }


class account_voucher(osv.Model):
    _inherit = 'account.voucher'

    _columns = {
        'transactions_id': fields.many2one('account.bank.transactions', 'Transferencia de dinero', readonly=True,
                                           states={'draft': [('readonly', False)]}),
        'type': fields.selection([('sale', 'Sale'),
                                  ('purchase', 'Purchase'),
                                  ('payment', 'Payment'),
                                  ('receipt', 'Receipt'),
                                  ('transfer', 'Transfer')],
                                 'Default Type', readonly=True, states={'draft': [('readonly', False)]}),
    }

    _document_type = {
        'sale': 'Sales Receipt',
        'purchase': 'Purchase Receipt',
        'payment': 'Supplier Payment',
        'receipt': 'Customer Payment',
        'transfer': 'Money Transfer',
        False: 'Payment',
    }

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        if context is None:
            context = {}
        res = super(account_voucher, self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency,
                                                               current_currency, context=context)
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        if voucher.type == 'transfer':
            if voucher.transactions_id.src_journal_id.id == voucher.journal_id.id:
                res['credit'] = voucher.paid_amount_in_company_currency
            else:
                res['debit'] = voucher.paid_amount_in_company_currency
            if res['debit'] < 0: res['credit'] = -res['debit']; res['debit'] = 0.0
            if res['credit'] < 0: res['debit'] = -res['credit']; res['credit'] = 0.0
            sign = res['debit'] - res['credit'] < 0 and -1 or 1
            res['currency_id'] = company_currency <> current_currency and current_currency or False
            res['amount_currency'] = company_currency <> current_currency and sign * voucher.amount or 0.0
        return res

class account_move(osv.osv):
    _inherit = "account.move"

    _columns = {
        'transactions_id': fields.many2one('account.bank.transactions', 'Transferencia de dinero', readonly=True,
                                           states={'draft': [('readonly', False)]}),
    }
