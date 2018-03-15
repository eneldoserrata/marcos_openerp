# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
{
    'name': 'Implementacion de ncf para Republica Dominicana by Marcos',
    'version': '0.0.1',
    'category': 'Sale',
    'description': """
        Para el uso de este modulo es nesesario utilizar una interface que hemos creado
        para conectar la impresora fiscal a la red para que de esta forma sea la impresora
        que pida la factura a imprimir ya con el NFC asigando
    """,
    'author': "Marcos Organizador de Negocios SRL",
    'website': "www.marcos.org.do",
    'depends': ['base',
                'web',
                'mail',
                'stock',
                'debit_credit_note',
                'point_of_sale',
                'purchase',
                'account',
                'marcos_pos_discount',
                'marcos_pos_customer',
                'marcos_pos_prod_avail',
                'account_cancel',
                'account_invoice_force_number'],
    'data': [
        "marcos_ncf_view.xml",
        "wizard/nc_from_stock.xml",
        "wizard/pos_payment_view.xml",
        "wizard/stock_account_move_view.xml",
        "wizard/pos_open_statement.xml",
        "cheque_popular_view.xml"
    ],
    'demo': [],
    'test': [],
    'qweb': ['static/src/xml/pos_ncf.xml', 'static/src/xml/base.xml'],
    'js': [
        'static/src/js/pos_ncf.js'
           ],
    'css': ['static/src/css/pos_ncf.css'],
    'installable': True,
    'active': False,
}
