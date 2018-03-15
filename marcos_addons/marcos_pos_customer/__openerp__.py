# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
{
    'name': 'Customizacion del punto de ventas',
    'version': '1.0',
    'category': 'Point Of Sale',
    'description': """
    Agrega funcionalidades al POS:
    - Seleccionar Clientes
    - Editar Clientes
    - Crear Notas de credito
    - Asignar numero de seria a productos
""",
    'author': "Marcos Organizador de Negocios SRL.",
    'website': "www.marcos.org.do",
    'depends': ['web', 'point_of_sale'],
    'data': [
        'product/product_view.xml',
        'pos_order/pos_order_view.xml'
    ],
    'demo': [],
    'test': [],
    'qweb': ['static/src/xml/pos_customer.xml'],
    'js': ['static/src/js/pos_customer.js',
           'static/src/js/jquery-barcode.js'],
    'css': ['static/src/css/pos_customer.css'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
