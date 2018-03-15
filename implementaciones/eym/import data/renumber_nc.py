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
cur.execute('select id, move_id, create_date from account_invoice where journal_id = 5 and state = %s order by create_date', ("paid",))
moves = cur.fetchall()

for move in moves:

    number = sock.execute(dbname, uid, pwd, 'ir.sequence', 'get', 'cf.nota.credito')
    print number
    invoice = cur.execute('update account_invoice set number = %s where id = %s', (number, move['id']))
    move = cur.execute('update account_move set name = %s where id = %s', (number, move['move_id']))
    conn.commit()