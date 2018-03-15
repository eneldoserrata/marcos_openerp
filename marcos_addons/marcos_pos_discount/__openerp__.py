# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
{
    'name': 'Descuentos en el POS',
    'version': '1.0',
    'category': 'Point of Sale',
    'description': """
    Este modulo agrega la funcionalidad de aplicar un descuento total a la factura.
    """,
    'author': "Marcos Organizador de Negocios SRL.",
    'website': "www.marcos.org.do",
    'depends': ['web', 'point_of_sale', 'base'],
    'data': [
        'security/pos_discount_security.xml',
        'security/ir.model.access.csv',
        'pos_discount/pos_discount_view.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': ['static/src/xml/pos_customer.xml'],
    'js': ['static/src/js/pos_customer.js'],
    'css': ['static/src/css/pos_customer.css'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: