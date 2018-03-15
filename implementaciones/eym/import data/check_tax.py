# -*- coding: utf-8 -*-
__author__ = "Eneldo Serrata"
import psycopg2
import xmlrpclib

sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')
uid = 1
pwd = 'admin'
dbname = "eymimportadores"



conn = psycopg2.connect(dbname='eymimportadores', user='eneldoserrata', password='marlboro', host="127.0.0.1")
cur = conn.cursor()
cur.execute('select move_id, ref, sum(tax_amount) from account_move_line where tax_code_id = 27 group by move_id, ref')
bases = cur.fetchall()

suma = 0
for base_imp in bases:
    sql = 'select move_id, ref, tax_amount from account_move_line where tax_code_id = 31 and move_id = %s' % base_imp[0]
    cur.execute(sql)
    impuestos = cur.fetchall()
    for impuesto in impuestos:
        b_i = float(base_imp[2]) * 0.18
        i_i = round(float(impuesto[2]), 2)
        diff = b_i-i_i
        suma += diff
        if abs(diff) > 1:
            print diff

print "suma", suma