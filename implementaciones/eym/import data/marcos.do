# -*- coding: utf-8 -*-
import psycopg2
import xmlrpclib
from psycopg2.extras import DictCursor



username = 'admin' #the user
pwd = 'CiscoSystem7970'      #the password of the user
dbname = 'eym'    #the database


# Get the uid
sock_common = xmlrpclib.ServerProxy ('http://localhost:8069/xmlrpc/common')
uid = sock_common.login(dbname, username, pwd)

#replace localhost with the address of the server
sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')

conn = psycopg2.connect(dbname='eym', user='eneldoserrata', password='marlboro', host="127.0.0.1")
cur = conn.cursor(cursor_factory=DictCursor)

cur.execute("select id, name, period_id from account_move_line where journal_id in (3,2,10,9) and account_id = 13 and name like 'POS%' and reconcile_id IS NULL")
invoices = cur.fetchall()




records = len(invoices)

for invoice in invoices:
    try:
        to_conciliate = []
        to_conciliate.append(invoice[2])
        to_conciliate.append(invoice[0])

        cur.execute("select id, name from account_move_line where journal_id in (25,41,42,36,18,37,43,38,33,31,32,44,45,55,56) and account_id = 13 and name like '%s%s'" % (invoice[1], ":%"))
        banks = cur.fetchall()

        for bank in banks:
            if len(bank):
                to_conciliate.append(bank[0])

        cur.execute("select id, name from account_move_line where journal_id in (28,34,17,29,30,35,26,46,48,52) and account_id = 13 and name like '%s%s'" % (invoice[1], ":%"))
        cashs = cur.fetchall()

        for cash in cashs:
            if len(cash):
                to_conciliate.append(cash[0])

        result = sock.execute(dbname, uid, pwd, 'account.move.line', 'reconcile', to_conciliate[1:], 'manual', False, to_conciliate[0], False, {})
        records -= 1
        print records, result
    except:
        print "Invoice: %s, Bank: %s, Cash: %s" % (invoice, banks, cashs)




