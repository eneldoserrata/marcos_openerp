# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
from openerp import netsvc


class account_bank_conciliation(osv.Model):
    _name = "account.bank.conciliation"

    def cal_diff(self, cr, uid, ids, field_name, arg, context=None):
        bank_transactions_obj = self.pool.get("account.bank.transactions")
        res = {}
        for cons in self.browse(cr, uid, ids, context=context):
            trans_total = sum([trans.src_amount for trans in cons.bank_transactions_ids if trans.state == "done"])
            res[cons.id] = (cons.amount_from + trans_total) - cons.amount_to
            return res

    def actualizar(self, cr, uid, *args, **kwargs):
        return True

    _columns = {
        'name': fields.char('Numero', size=32, required=True, readonly=True),
        "company_id": fields.many2one('res.company', u'Compañia', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        "jornal_id": fields.many2one("account.journal", "Diario", required=True),
        "amount_from": fields.float("Saldo inicial", required=True),
        "amount_to": fields.float("Saldo Final", required=True),
        "date_from": fields.date("Fecha inicial", required=True),
        "date_to": fields.date("Fecha final", required=True),
        "state": fields.selection([("draft", "Borrador"), ("progress", "En Proceso"), ("confirm", "Confirmado")]),
        "bank_transactions_ids": fields.one2many("account.bank.transactions", "conciliation_id", u"Transacciones", readonly=True),
        "diference": fields.function(cal_diff, type="float", string="Diferencia")
    }

    _defaults = {'state': 'draft',
                 'company_id': lambda s, cr, u, c: s.pool.get('res.users').browse(cr, u, u).company_id.id,
                 "name": "/"}

    def import_transactions(self, cr, uid, ids, context=None):
        bank_transactions_obj = self.pool.get("account.bank.transactions")
        for conciliation in self.browse(cr, uid, ids):
            trans_list_ids = bank_transactions_obj.search(cr, uid, [("state", "!=", "done"), ("conciliation_id", '=', False), ("date", "<=", conciliation.date_to)])
            bank_transactions_obj.write(cr, uid, trans_list_ids, {"conciliation_id": conciliation.id})
        return True

    def create(self, cr, uid, values, context=None):
        values.update({"name": self.pool.get('ir.sequence').get(cr, uid, 'account.conciliation')})
        result = super(account_bank_conciliation, self).create(cr, uid, values, context=context)
        return result

    def confirm(self, cr, uid, ids, context=None):
        pass


class account_bank_transactions(osv.Model):
    _name = 'account.bank.transactions'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'name desc'

    def _get_balance(self, src_journal, dst_journal, company):
        src_balance = dst_balance = 0.0
        if src_journal.default_credit_account_id.id == src_journal.default_debit_account_id.id:
            if not src_journal.currency or company.currency_id.id == src_journal.currency.id:
                src_balance = src_journal.default_credit_account_id.balance
            else:
                src_balance = src_journal.default_credit_account_id.foreign_balance
        else:
            if not src_journal.currency or company.currency_id.id == src_journal.currency.id:
                src_balance = src_journal.default_debit_account_id.balance - src_journal.default_credit_account_id.balance
            else:
                src_balance = src_journal.default_debit_account_id.foreign_balance - src_journal.default_credit_account_id.foreign_balance
        if dst_journal.default_credit_account_id.id == dst_journal.default_debit_account_id.id:
            if not dst_journal.currency or company.currency_id.id == dst_journal.currency.id:
                dst_balance = dst_journal.default_credit_account_id.balance
            else:
                dst_balance = dst_journal.default_credit_account_id.foreign_balance
        else:
            if not dst_journal.currency or company.currency_id.id == dst_journal.currency.id:
                dst_balance = dst_journal.default_debit_account_id.balance - dst_journal.default_credit_account_id.balance
            else:
                dst_balance = dst_journal.default_debit_account_id.foreign_balance - dst_journal.default_credit_account_id.foreign_balance

        return (src_balance, dst_balance)

    def _balance(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for trans in self.browse(cr, uid, ids, context=context):
            src_balance, dst_balance = self._get_balance(trans.src_journal_id, trans.dst_journal_id, trans.company_id)
            exchange = False
            if trans.dst_journal_id.currency.id != trans.src_journal_id.currency.id:
                exchange = True
            res[trans.id] = {
                'src_balance': src_balance,
                'dst_balance': dst_balance,
                'exchange': exchange,
                'exchange_inv': (trans.exchange_rate and 1.0 / trans.exchange_rate or 0.0)
            }
        return res

    STATE_SELECTION = [
        ('draft', 'Borrador'),
        ('confirm', 'Confirmado'),
        ('done', 'Conciliado'),
        ('cancel', 'Cancelado'),
    ]

    _columns = {
        'company_id': fields.many2one('res.company', u'Compañia', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'name': fields.char('Numero', size=32, required=True, readonly=True),
        # 'name': fields.char('Numero', size=32, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Fecha', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'origin': fields.char('Referencia', size=128, readonly=True, states={'draft': [('readonly', False)]},
                              help="Referecia"),
        'bank_statement_id': fields.many2one('account.bank.statement', string='Origen', readonly=True,
                                             states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True,
                                               states={'draft': [('readonly', False)]}),
        'voucher_ids': fields.one2many('account.voucher', 'transactions_id', string='Payments', readonly=True,
                                       states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'src_journal_id': fields.many2one('account.journal', 'Diario de origen', required=True,
                                          domain=[('type', 'in', ['cash', 'bank']), ('journal_user', '=', True)],
                                          select=True, readonly=True,
                                          states={'draft': [('readonly', False)]}),
        'src_partner_id': fields.many2one('res.partner', 'Relacionado', select=True),
        'src_balance': fields.function(_balance, digits_compute=dp.get_precision('Account'),
                                       string='Balance actual de origen', type='float', readonly=True, multi='balance',
                                       help="Include all account moves in draft and confirmed state"),
        'src_amount': fields.float('Balance de origen', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}),
        'src_have_partner': fields.related('src_journal_id', 'have_partner', type='boolean', string='Have Partner',
                                           readonly=True),
        'dst_journal_id': fields.many2one('account.journal', 'Diario de destino', required=True,
                                          domain=[('type', '=', 'bank')], select=True, readonly=True,
                                          states={'draft': [('readonly', False)]}),
        'dst_partner_id': fields.many2one('res.partner', 'Relacionado de destino', select=True),
        'dst_balance': fields.function(_balance, digits_compute=dp.get_precision('Account'),
                                       string='Balance actual de destino', type='float', readonly=True, multi='balance',
                                       help="Include all account moves in draft and confirmed state"),
        'dst_amount': fields.float('Balance de destino', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}),
        'dst_have_partner': fields.related('dst_journal_id', 'have_partner', type='boolean', string='Have Partner',
                                           readonly=True),
        'exchange_rate': fields.float('Exchange Rate', digits_compute=dp.get_precision('Exchange'), readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'exchange': fields.function(_balance, string='Have Exchange', type='boolean', readonly=True, multi='balance'),
        'exchange_inv': fields.function(_balance, string='1 / Exchange Rate', type='float',
                                        digits_compute=dp.get_precision('Exchange'), readonly=True, multi='balance'),
        'adjust_move': fields.many2one('account.move', 'Adjust Move', readonly=True,
                                       help="Adjust move usually by difference in the money exchange"),
        'state': fields.selection(STATE_SELECTION, string='State', readonly=True),
        'move_ids': fields.one2many('account.move', 'transactions_id', string='Payments', readonly=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        "conciliation_id": fields.many2one("account.bank.conciliation", u"Conciliación")

    }
    _defaults = {
        # 'name': lambda s, cr, u, c: s.pool.get('ir.sequence').get(cr, u, 'account.conciliation'),
        'name': "/",
        'company_id': lambda s, cr, u, c: s.pool.get('res.users').browse(cr, u, u).company_id.id,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'exchange_rate': 1.0,
        'exchange_inv': 1.0,
        'state': 'draft',
    }
    _sql_constraints = [('name_unique', 'unique(company_id,name)', _('El número debe ser único!'))]

    def unlink(self, cr, uid, ids, context=None):
        for trans in self.browse(cr, uid, ids, context=context):
            if trans.state not in ('draft'):
                raise osv.except_osv(_('User Error!'), _('You cannot delete a not draft transfer "%s"') % trans.name)
        return super(account_bank_transactions, self).unlink(cr, uid, ids, context=context)

    def copy(self, cr, uid, id, defaults, context=None):
        defaults['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.conciliation')
        defaults['voucher_ids'] = []
        return super(account_bank_transactions, self).copy(cr, uid, id, defaults, context=context)

    def onchange_amount(self, cr, uid, ids, field, src_amount, dst_amount, exchange_rate):
        res = {'value': {}}
        if field == 'src_amount':
            res['value']['src_amount'] = src_amount
            res['value']['dst_amount'] = src_amount * exchange_rate
            res['value']['exchange_rate'] = exchange_rate
            res['value']['exchange_inv'] = exchange_rate and 1.0 / exchange_rate or 0.0
        elif field == 'dst_amount':
            res['value']['src_amount'] = exchange_rate and dst_amount / exchange_rate or 0.0
            res['value']['dst_amount'] = dst_amount
            res['value']['exchange_rate'] = exchange_rate
            res['value']['exchange_inv'] = exchange_rate and 1.0 / exchange_rate or 0.0
        elif field == 'exchange_rate':
            res['value']['src_amount'] = src_amount
            res['value']['dst_amount'] = src_amount * exchange_rate
            res['value']['exchange_rate'] = exchange_rate
            res['value']['exchange_inv'] = exchange_rate and 1.0 / exchange_rate or 0.0
        return res

    def onchange_journal(self, cr, uid, ids, src_journal_id, dst_journal_id, date, exchange_rate, src_amount):
        res = {'value': {}}
        if not (src_journal_id and dst_journal_id):
            return res
        src_journal = self.pool.get('account.journal').browse(cr, uid, src_journal_id)
        dst_journal = self.pool.get('account.journal').browse(cr, uid, dst_journal_id)
        res['value']['src_balance'], res['value']['dst_balance'] = self._get_balance(src_journal, dst_journal,
                                                                                     src_journal.company_id)
        res['value']['exchange'] = (src_journal.currency.id != dst_journal.currency.id)
        res['value']['src_have_partner'], res['value'][
            'dst_have_partner'] = src_journal.have_partner, dst_journal.have_partner
        res['value']['exchange_rate'] = exchange_rate
        if res['value']['exchange']:
            res['value']['exchange_rate'] = (
                                                src_journal.currency and src_journal.currency.rate or src_journal.company_id.currency_id.rate) and (
                                                (
                                                    dst_journal.currency and dst_journal.currency.rate or dst_journal.company_id.currency_id.rate) / (
                                                    src_journal.currency and src_journal.currency.rate or src_journal.company_id.currency_id.rate)) or 0.0
        else:
            res['value']['exchange_rate'] = 1.0
        res['value']['exchange_inv'] = res['value']['exchange_rate'] and (1.0 / res['value']['exchange_rate']) or 0.0
        res['value']['dst_amount'] = res['value']['exchange_rate'] * src_amount
        return res

    def action_confirm(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        for trans in self.browse(cr, uid, ids, context=context):
            sval = {}
            sval['transactions_id'] = trans.id
            sval['type'] = 'transfer'
            sval['company_id'] = trans.company_id.id
            sval['reference'] = trans.name + str(trans.origin and (' - ' + trans.origin) or '')
            sval['line_ids'] = [(0, 0, {})]
            sval['line_ids'][0][2]['account_analytic_id'] = trans.account_analytic_id and trans.account_analytic_id.id or 0
            sval['line_ids'][0][2]['name'] = trans.origin
            sval['journal_id'] = trans.src_journal_id.id
            sval['account_id'] = trans.src_journal_id.default_credit_account_id.id
            sval['payment_rate'] = trans.src_journal_id.currency.id and trans.company_id.currency_id.id <> trans.src_journal_id.currency.id and trans.exchange_rate or 1.0
            sval['payment_rate_currency_id'] = trans.dst_journal_id.currency.id or trans.company_id.currency_id.id
            sval['line_ids'][0][2]['amount'] = sval['amount'] = trans.src_amount
            sval['line_ids'][0][2]['type'] = 'dr'
            sval['line_ids'][0][2]['account_id'] = trans.dst_journal_id.default_debit_account_id.id

            if trans.src_partner_id.id ^ trans.dst_partner_id.id:
                sval['partner_id'] = trans.src_have_partner and trans.src_partner_id.id or trans.dst_partner_id.id
            else:
                sval['partner_id'] = trans.src_have_partner and trans.src_partner_id.id or trans.company_id.partner_id.id
                sval['line_ids'][0][2]['account_id'] = trans.src_journal_id.account_transit.id

            sval_id = voucher_obj.create(cr, uid, sval, context=context)
            voucher_obj.proforma_voucher(cr, uid, [sval_id], context=context)
            move_id = voucher_obj.browse(cr, uid, sval_id).move_id.id
            move_obj = self.pool.get("account.move")
            move_obj.button_validate(cr, uid, [move_id], context=None)
        return self.write(cr, uid, ids, {'state': 'confirm'}, context=context)

    def action_done(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')

        for trans in self.browse(cr, uid, ids, context=context):
            dval = {}
            dval['transactions_id'] = trans.id
            dval['type'] = 'transfer'
            dval['company_id'] = trans.company_id.id
            dval['reference'] = trans.name + str(trans.origin and (' - ' + trans.origin) or '')
            dval['line_ids'] = [(0, 0, {})]
            dval['line_ids'][0][2]['account_analytic_id'] = trans.account_analytic_id and trans.account_analytic_id.id or 0
            dval['line_ids'][0][2]['name'] = trans.origin
            dval['journal_id'] = trans.dst_journal_id.id
            dval['account_id'] = trans.dst_journal_id.default_debit_account_id.id
            dval['payment_rate'] = trans.dst_journal_id.currency.id and trans.company_id.currency_id.id <> trans.dst_journal_id.currency.id and trans.exchange_inv or 1.0
            dval['payment_rate_currency_id'] = trans.src_journal_id.currency.id or trans.company_id.currency_id.id
            dval['line_ids'][0][2]['amount'] = dval['amount'] = trans.dst_amount
            dval['line_ids'][0][2]['type'] = 'cr'
            dval['partner_id'] = trans.dst_have_partner and trans.dst_partner_id.id or trans.company_id.partner_id.id
            dval['line_ids'][0][2]['account_id'] = trans.src_journal_id.account_transit.id
            dval_id = voucher_obj.create(cr, uid, dval, context=context)
            voucher_obj.proforma_voucher(cr, uid, [dval_id], context=context)
            move_id = voucher_obj.browse(cr, uid, dval_id).move_id.id
            move_obj = self.pool.get("account.move")
            move_obj.button_validate(cr, uid, [move_id], context=None)

            paid_amount = []
            for voucher in trans.voucher_ids:
                # voucher.state == 'draft' and voucher_obj.proforma_voucher(cr, uid, [voucher.id], context=context)
                sign = (voucher.journal_id.id == trans.src_journal_id.id) and 1 or -1
                paid_amount.append(sign * voucher_obj._paid_amount_in_company_currency(cr, uid, [voucher.id], '', '')[voucher.id])
                # paid_amount.append(sign * voucher.paid_amount_in_company_currency)
            sum_amount = sum(paid_amount)

            if len(paid_amount) > 1 and sum_amount != 0.0:
                periods = self.pool.get('account.period').find(cr, uid)
                move = {}
                move['journal_id'] = trans.dst_journal_id.id
                move['period_id'] = periods and periods[0] or False
                move['ref'] = trans.name + str(trans.origin and (' - ' + trans.origin) or '')
                move['date'] = trans.date
                move['line_id'] = [(0, 0, {}), (0, 0, {})]
                move['line_id'][0][2]['name'] = trans.name
                move['line_id'][1][2]['name'] = trans.name
                if sum_amount > 0:
                    move['line_id'][0][2]['account_id'] = trans.dst_journal_id.default_debit_account_id.id
                    move['line_id'][1][2]['account_id'] = trans.src_journal_id.account_transit.id  # trans.company_id.income_currency_exchange_account_id.id
                    move['line_id'][0][2]['debit'] = sum_amount
                    move['line_id'][1][2]['credit'] = sum_amount
                else:
                    move['line_id'][0][2]['account_id'] = trans.dst_journal_id.default_credit_account_id.id
                    move['line_id'][1][2]['account_id'] = trans.src_journal_id.account_transit.id  # trans.company_id.expense_currency_exchange_account_id.id
                    move['line_id'][1][2]['debit'] = -1 * sum_amount
                    move['line_id'][0][2]['credit'] = -1 * sum_amount

                move_id = move_obj.create(cr, uid, move, context=context)
                self.write(cr, uid, [trans.id], {'adjust_move': move_id}, context=context)
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        move_obj = self.pool.get('account.move')
        for trans in self.browse(cr, uid, ids, context=context):
            for voucher in trans.voucher_ids:
                voucher_obj.cancel_voucher(cr, uid, [voucher.id], context=context)
                voucher_obj.unlink(cr, uid, [voucher.id], context=context)
            trans.adjust_move and move_obj.unlink(cr, uid, [trans.adjust_move.id], context=context)
        result = self.write(cr, uid, ids, {'state': 'cancel', 'conciliation_id': False}, context=context)
        return result

    def create(self, cr, uid, values, context=None):
        values.update({"name": self.pool.get('ir.sequence').get(cr, uid, 'account.trasaction')})
        result = super(account_bank_transactions, self).create(cr, uid, values, context=context)
        return result



