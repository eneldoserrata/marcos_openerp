# -*- coding: utf-8 -*-
{
    'name': 'Implementacion de ncf para Republica Dominicana by Marcos',
    'version': '0.0.1',
    'category': 'Sale',
    'description': """
        Para el uso de este modulo es nesesario utilizar una interface que hemos creado
        para conectar la impresora fiscal a la red para que de esta forma sea la impresora
        que pida la factura a imprimir ya con el NFC asigando
    """,
    'author': 'Eneldo Serrata',
    'depends': ['base', 'web', 'mail', 'debit_credit_note', 'point_of_sale', 'purchase'],
    'data': ['pos_ncf/pos_ncf_view.xml'],
    'demo': [],
    'test': [],
    'qweb': ['static/src/xml/pos_ncf.xml', 'static/src/xml/base.xml'],
    'js': ['static/src/js/pos_ncf.js'],
    'css': ['static/src/css/pos_ncf.css'],
    'installable': True,
    'active': False,
}