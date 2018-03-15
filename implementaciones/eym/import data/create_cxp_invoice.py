# -*- coding: utf-8 -*-
import psycopg2
import xmlrpclib
from psycopg2.extras import DictCursor

sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')
uid = 1
pwd = 'CiscoSystem7970'
dbname = "eymimportadores"

conn = psycopg2.connect(dbname='eymimportadores', user='postgres', password='marlboro', host="127.0.0.1")

cur = conn.cursor(cursor_factory=DictCursor)
cur.execute('select id from account_move where journal_id = 19 and period_id = 4')

moves = cur.fetchall()

for move in moves:
    cur.execute('select * from account_move_line where move_id = %s', move)
    lines = cur.fetchall()
    for line in lines:
        if line[u"credit"]:
            vals = {u'account_id': line[u"account_id"],
                     u'check_total': 0,
                     u'child_ids': [[6, False, []]],
                     u'comment': u"factura importada de expert",
                     u'company_id': 1,
                     u'currency_id': 74,
                     u'date_due': u'2014-08-19',
                     u'date_invoice': u'2014-03-31',
                     u'fiscal_position': 13,
                     u'internal_number': False,
                     u'invoice_line': [[0,
                                        False,
                                        {u'account_analytic_id': False,
                                         u'account_id': 101,
                                         u'asset_category_id': False,
                                         u'discount': 0,
                                         u'invoice_line_tax_id': [[6, False, []]],
                                         u'name': u'CXP iniciales',
                                         u'price_unit': float(line[u"credit"]),
                                         u'product_id': 4420,
                                         u'quantity': 1,
                                         u'uos_id': 1}]],
                     u'journal_id': line[u"journal_id"],
                     u'message_follower_ids': False,
                     u'message_ids': False,
                     u'name': False,
                     u'ncf_required': True,
                     u'origin': False,
                     u'parent_id': False,
                     u'partner_bank_id': False,
                     u'partner_id': line[u"partner_id"],
                     u'payment_term': 5,
                     u'period_id': False,
                     u'reference': line[u"name"],
                     u'reference_type': u'09',
                     u'supplier_invoice_number': u'',
                     u'tax_line': [],
                     u'user_id': 1}
            try:
                context = {u'lang': u'es_DO', u'tz': u'America/Santo_Domingo', u'uid': 1, u'journal_type': u'purchase', u'default_type': u'in_invoice', u'type': u'in_invoice'}
                result = sock.execute(dbname, uid, pwd, 'account.invoice', 'create', vals, context)
                print result
            except Exception, e:
                print e
                print vals
