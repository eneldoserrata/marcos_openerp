# -*- coding: utf-8 -*-
__author__ = "Eneldo Serrata"
import psycopg2
import xmlrpclib

sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')
uid = 1
pwd = 'admin'
dbname = "eymimportadores"



conn = psycopg2.connect(dbname='eymimportadores', user='postgres', password='marlboro', host="127.0.0.1")
cur = conn.cursor()
cur.execute('select "IDCLIENTE", "CLI_CODIGO", "CLI_NOMBRE" from "CLIENTES" where "CLIENTES"."CLI_BALANCE" > 0')
clientes = cur.fetchall()

for cliente in clientes:
    idcliente = str(cliente[0])
    cliente_ref = str(cliente[1])
    cliente_nombre = str(cliente[2])
    cur.execute("SELECT id FROM res_partner WHERE res_partner.ref = '%s' AND res_partner.customer = TRUE" % (cliente_ref))
    res_partner_id = cur.fetchall()

    if len(res_partner_id) > 0:
        partner_id = res_partner_id[0][0]

        values = {}
        values["ref"] = cliente_nombre
        values["journal_id"] = 22
        values["period_id"] = 4
        values["narration"] = False
        values["date"] = u'2014-03-31'
        values["partner_id"] = partner_id
        values["to_check"] = True
        values["line_id"] = []

        cur = conn.cursor()
        cur.execute('SELECT * FROM "FACTURAS" WHERE "IDCLIENTE" = %s' % idcliente)
        facturas = cur.fetchall()
        ncf = False
        balance_total = 0
        for factura in facturas:
            debit_line = []
            if factura[36] == 1:
                ncf = "A0100100101%s" % str(factura[35]).zfill(8)
            elif factura[36] == 2:
                ncf = "A0100100102%s" % str(factura[35]).zfill(8)
            elif factura[36] == 14:
                ncf = "A0100100114%s" % str(factura[35]).zfill(8)
            elif factura[36] == 15:
                ncf = "A0100100115%s" % str(factura[35]).zfill(8)
            balance = float(factura[17]-factura[18])

            if balance <= 0:
                continue

            debit_line = [0, False, {u'analytic_account_id': False,
                                     u'tax_code_id': False,
                                     u'tax_amount': 0,
                                     u'name': ncf or False,
                                     u'currency_id': False,
                                     u'credit': 0,
                                     u'date_maturity': str(factura[22]),
                                     u'debit': balance,
                                     u'amount_currency': 0,
                                     u'partner_id': partner_id,
                                     u'account_id': 13}]
            balance_total += balance
            values["line_id"].append(debit_line)

        values["line_id"].append([0, False, {u'analytic_account_id': False,
                                             u'tax_code_id': False,
                                             u'tax_amount': 0,
                                             u'name': u'venta',
                                             u'currency_id': False,
                                             u'credit': balance_total,
                                             u'date_maturity': False,
                                             u'debit': 0,
                                             u'amount_currency': 0,
                                             u'partner_id': partner_id,
                                             u'account_id': 87}])

        try:
            result = sock.execute(dbname, uid, pwd, 'account.move', 'create', values)
            print result
        except Exception, e:
            print values
            print e



cur.close()
conn.close()


        # insert_account_move = "insert into account_move (id,  name, partner_id, company_id, journal_id, state,   period_id, narration, date,         ref,  to_check, create_uid, create_date, write_uid, write_date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        # values_account_move = (
        # 278, '/', '20035', '1', 22, 'draft', 4, None, '2014-03-31', None, False, 1, None, 1, None)
        # cur.execute(insert_account_move, values_account_move)
        #
        # insert_account_journal_period = "insert into account_journal_period (id, active, state,   period_id, name,            journal_id, company_id, create_uid, create_date, write_uid, write_date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        # values_account_journal_period = (14, 'True', 'draft', 4, 'cxcin:03/2014', 22, 1, 1, None, 1, None)
        # cur.execute(insert_account_journal_period, insert_account_journal_period)



# insert into "account_move" (id,"name","partner_id","company_id","journal_id","state","period_id","narration","date",      "ref","to_check",create_uid,create_date,write_uid,write_date) values (278,'/',   '20035',       '1',          22,         'draft', 4,          NULL,      '2014-03-31',NULL, 'False',    1,(now() at time zone 'UTC'),1,(now() at time zone 'UTC'))
#
# insert into "account_journal_period" (id,"active","state","period_id","name",           "journal_id", "company_id",create_uid,create_date,write_uid,write_date)
# values (14,'True',  'draft', 4,         'cxcin:03/2014',   22,           1,          1,(now() at time zone 'UTC'),1,(now() at time zone 'UTC'))
#
#
# insert into "account_move_line" (id,  "state", "ref", "account_id", "draft_assigned","journal_id","currency_id","date_maturity","period_id","amount_currency","date",       "partner_id","move_id","blocked","analytic_account_id","tax_amount", "name",                "centralisation","company_id","tax_code_id","credit",   "state", "debit", "date_created",create_uid,create_date,write_uid,write_date) values
#                                 (728, 'valid', "",  87,           'False',           '22',        NULL,          NULL,          '4',        '0.00',           '2014-03-31', 20035,       278,      'False',   NULL,                '0.00',       'A010010010100000002',   'normal',        '1',          NULL,        '10000.00', 'draft', '0.00',   '2014-04-12', 1,(now() at time zone 'UTC'),1,(now() at time zone 'UTC'))
#
# insert into "account_move_line" (id,  "state", "ref", "account_id","draft_assigned","journal_id","currency_id","date_maturity","period_id","amount_currency","date",      "partner_id","move_id","blocked","analytic_account_id","tax_amount","name",               "centralisation","company_id","tax_code_id","credit","state","debit","date_created","ref",create_uid,create_date,write_uid,write_date)
#                          values (729, 'valid', "", 13,          'False',             '22',         NULL,        '2014-04-16',   '4',        '0.00',           '2014-03-31',20035,  278,'False',NULL,'0.00',                                       'A010010010100000002','normal',         '1',NULL,'0.00','draft','10000.00','2014-04-12',NULL,1,(now() at time zone 'UTC'),1,(now() at time zone 'UTC'))

a = {u'ref': False,
     u'journal_id': 22,
     u'line_id': [[0, False, {u'analytic_account_id': False,
                              u'tax_code_id': False,
                              u'tax_amount': 0,
                              u'name': u'A010010010100000002',
                              u'currency_id': False,
                              u'credit': 10500,
                              u'date_maturity': False,
                              u'debit': 0,
                              u'amount_currency': 0,
                              u'partner_id': 20674,
                              u'account_id': 87}],
                  [0, False, {u'analytic_account_id': False,
                              u'tax_code_id': False,
                              u'tax_amount': 0,
                              u'name': u'A010010010100000002',
                              u'currency_id': False,
                              u'credit': 0,
                              u'date_maturity': u'2014-04-30',
                              u'debit': 10500,
                              u'amount_currency': 0,
                              u'partner_id': 20674,
                              u'account_id': 13}]],
     u'period_id': 4,
     u'narration': False,
     u'date': u'2014-03-31',
     u'partner_id': False,
     u'to_check': False}