# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc, tools
import time

class pos_discount(osv.Model):
    _name = "pos.group.discount"
    _columns = {
        'name': fields.char('Nombre', size=124),
        'amount': fields.float('Porciento (%)'),
        'users': fields.many2many('res.users', 'pos_discount_users', 'discount_id', 'user_id', string='Agregar usuario')
    }
