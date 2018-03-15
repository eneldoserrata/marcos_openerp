# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import netsvc
import time
import datetime
import itertools
import operator
import logging

_logger = logging.getLogger(__name__)


class pos_session(osv.Model):
    _inherit = "pos.session"

    def wkf_action_close(self, cr, uid, ids, context=None):
        result = super(pos_session, self).wkf_action_close(cr, uid, ids, context=context)
        transactions_obj = self.pool.get("account.bank.transactions")
        wf_service = netsvc.LocalService("workflow")

        # self.reconcilie_pos_invoice(cr, uid, ids, context=context)
        for session in self.browse(cr, uid, ids):
            for statement in session.statement_ids:

                try:
                    bank_journal_destination = statement.journal_id.dst_bank_id.journal_id.id
                except:
                    raise osv.except_osv('Configuracion pendiente!', 'Debe de configurar un banco de destino para cada diario de pago..')

                if statement.journal_id.electronic_payment:
                    transaction_amount = self.make_electronic_charge(cr, uid, statement, context=context)
                else:
                    transaction_amount = statement.balance_end


                account_bank_transaction_values = {u'bank_statement_id': statement.id,
                                                     u'company_id': statement.company_id.id,
                                                     u'date': statement.date,
                                                     u'dst_amount': transaction_amount,
                                                     u'dst_journal_id': bank_journal_destination,
                                                     u'dst_partner_id': False,
                                                     u'message_follower_ids': False,
                                                     u'message_ids': False,
                                                     u'move_ids': [],
                                                     u'origin': False,
                                                     u'src_amount': transaction_amount,
                                                     u'src_journal_id': statement.journal_id.id,
                                                     u'src_partner_id': False,
                                                     u'voucher_ids': []}
                new_bank_transaction_id = transactions_obj.create(cr, uid, account_bank_transaction_values)
                wf_service.trg_validate(uid, 'account.bank.transactions', new_bank_transaction_id, 'transfer_confirm', cr)

        return result


    def make_electronic_charge(self, cr, uid, statement, context=None):
        """
        this method take configuration from journal and modify the move acoording to parameter
        """
        account_move_line_obj = self.pool.get("account.move.line")
        default_account = statement.journal_id.default_debit_account_id
        save_charge_account_id = statement.journal_id.save_charge_account_id
        save_charge_percent = statement.journal_id.save_charge_percent
        tax_retention_account_id = statement.journal_id.tax_retention_account_id
        tax_retention_percent =  statement.journal_id.tax_retention_percent
        tax_retention_tax_code = statement.journal_id.tax_code_id

        total_charge = round((statement.balance_end * save_charge_percent), 2)
        total_tax_retention = round((statement.balance_end * tax_retention_percent), 2)
        total_transaction_amount = round(statement.balance_end-(total_charge + total_tax_retention), 2)

        for move_line in statement.move_line_ids:
            if move_line.account_id.id == default_account.id:
                charge = round((move_line.debit * save_charge_percent), 2)
                tax_retention = round((move_line.debit * tax_retention_percent), 2)
                total_retention = round(charge + tax_retention, 2)
                template_move_line = {'account_id': False,
                                      'amount_currency': False,
                                      'analytic_account_id': False,
                                      'credit': 0.0,
                                      'currency_id': False,
                                      'date': move_line.date,
                                      'debit': 0.0,
                                      'journal_id': move_line.journal_id.id,
                                      'move_id': move_line.move_id.id,
                                      'name': move_line.name,
                                      'partner_id': move_line.partner_id.id,
                                      'period_id': move_line.period_id.id,
                                      'ref': move_line.ref,
                                      'statement_id': move_line.statement_id.id}
                for i in range(3):
                    if i == 0:
                        template_move_line.update({"account_id": save_charge_account_id.id, "debit": charge, "credit": 0.0})
                    elif i == 1:
                        template_move_line.update({"account_id": tax_retention_account_id.id, "debit": tax_retention, "credit": 0.0, "tax_code_id": tax_retention_tax_code.id, "tax_amount": tax_retention * -1})
                    else:
                        template_move_line.update({"account_id": default_account.id, "debit": 0.0, "credit": total_retention, "tax_code_id": False, "tax_amount": False})
                    account_move_line_obj.create(cr, uid, template_move_line, context=context)

        return total_transaction_amount