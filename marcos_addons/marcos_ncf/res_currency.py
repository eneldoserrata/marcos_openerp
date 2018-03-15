# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv


class res_currency_rate(osv.Model):
    _inherit = "res.currency.rate"

    _columns = {
        'rate': fields.float('Rate', digits=(12, 17), help='The rate of the currency to the currency of rate 1')
    }
