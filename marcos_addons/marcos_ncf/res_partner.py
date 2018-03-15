# -*- encoding: utf-8 -*-
##############################################################################
#
#    Marcos Organizador de Negocios SRL.
#    Copyright (C) 2013-2014
#
##############################################################################
from openerp.osv.orm import browse_null
from idvalidator import is_identification
from openerp.osv import osv, fields
import redis
from redis.exceptions import RedisError
import json


class res_partner(osv.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    def _check_unique_ref(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids, context=context)[0]
        if partner.customer or partner.supplier:
            if partner.is_company and not partner.ref:
                return False
            elif partner.is_company and isinstance(partner.property_account_position, browse_null):
                return False
            elif partner.is_company and is_identification(partner.ref):
                return True
            elif partner.is_company is False:
                return True
        else:
            return True

    _columns = {
        'invoice_method': fields.selection([('manual', 'Se digitaran las facturas manualmente'),
                                            ('order', 'El proveedor envia factura definitiva'),
                                            ('picking', 'El proveedor envia orden de entrega y luego envia la factura')],
                                            'Invoicing Control',
                                           help="Based on Purchase Order lines: place individual lines in 'Invoice Control > Based on P.O. lines' from where you can selectively create an invoice.\n" \
                                            "Based on generated invoice: create a draft invoice you can validate later.\n" \
                                            "Bases on incoming shipments: let you create an invoice when receptions are validated."
        ),
        'multiple_company_rnc': fields.boolean(u"RNC para varias compañias", help=u"Esto permite poder utilizar el RNC en varios registros de compañias")
    }

    _constraints = [
        (osv.osv._check_recursion, 'You cannot create recursive Partner hierarchies.', ['parent_id']),
        # (_check_unique_ref, u"Los datos fiscales no son valido revise RNC/Cédula y la posición fiscal", [u"Rnc/Cédula"]),
    ]

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):

            self.check_access_rights(cr, uid, 'read')
            where_query = self._where_calc(cr, uid, args, context=context)
            self._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            # TODO: simplify this in trunk with `display_name`, once it is stored
            # Perf note: a CTE expression (WITH ...) seems to have an even higher cost
            #            than this query with duplicated CASE expressions. The bulk of
            #            the cost is the ORDER BY, and it is inevitable if we want
            #            relevant results for the next step, otherwise we'd return
            #            a random selection of `limit` results.
            query = ('''SELECT res_partner.id FROM res_partner
                                  LEFT JOIN res_partner company
                                       ON res_partner.parent_id = company.id'''
                + where_str + ''' (res_partner.email ''' + operator + ''' %s OR  res_partner.ref ''' + operator + ''' %s OR
                      CASE
                           WHEN company.id IS NULL OR res_partner.is_company
                               THEN res_partner.name
                           ELSE company.name || ', ' || res_partner.name
                      END ''' + operator + ''' %s)
                ORDER BY
                      CASE
                           WHEN company.id IS NULL OR res_partner.is_company
                               THEN res_partner.name
                           ELSE company.name || ', ' || res_partner.name
                      END''')


            where_clause_params += [search_name, search_name]
            where_clause_params.append(search_name)
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)

            cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], cr.fetchall())

            if ids:
                return self.name_get(cr, uid, ids, context)
            else:
                return []
        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    def create(self, cr, uid, vals, context=None):
        try:
            supplier = context.get('search_default_supplier', False)
            customer = context.get('search_default_customer', False)
            r = redis.StrictRedis(host='localhost', port=6379, db=0)

            if vals.get('ref', False) and not len(vals['ref']) in [9, 11]:
                raise osv.except_osv(u"Debe colocar un numero de RNC/Cedula valido!", u"001")

            elif vals['name'].isdigit() and not len(vals['name']) in [9, 11]:
                raise osv.except_osv(u"Debe colocar un numero de RNC/Cedula valido!", u"002")

            elif (vals.get('ref', False) and self.search(cr, uid, [('ref', '=', vals['ref']), ('multiple_company_rnc', '=', False)])) or \
                    (vals['name'] and self.search(cr, uid, [('ref', '=', vals['name']), ('multiple_company_rnc', '=', False)])):
                raise osv.except_osv(u"Es relacionado ya ha sido registrado! Si quiere utilizar varios relacionados con mismo RNC/Cedula debe indicarlo en el campo --RNC para varias compañias--", u"003")
            elif vals['name'].isdigit() and len(vals['name']) in [9, 11]:
                data = json.loads(r.get(vals['name']))
                if data:
                    vals['ref'] = vals['name']
                    vals['name'] = data['name']
                    vals['street'] = u"%s %s" % (data['street'], data['number'])
                    vals['street1'] = data['sector']
                    vals["comment"] = u"Creada el %s, actividad %s" % (data['establishment'], data['description'])
                    if len(vals['ref']) == 9:
                        vals['is_company'] = True

                    if customer:
                        vals['property_account_position'] = 1
                    elif supplier:
                        vals["property_account_position"] = 13
                else:
                    raise osv.except_osv(u"El numero de RNC/Cedula no es valido", u"")
            elif vals.get('ref', False) and r.get(vals['ref']):
                data = json.loads(r.get(vals['ref']))
                if data:
                    vals['name'] = data['name']
                    vals['street'] = u"%s %s" % (data['street'], data['number'])
                    vals['street1'] = data['sector']
                    vals["comment"] = u"Creada el %s, actividad %s" % (data['establishment'], data['description'])
                    if len(vals['ref']) == 9:
                        vals['is_company'] = True
                        if customer:
                            vals['property_account_position'] = 1
                        elif supplier:
                            vals["property_account_position"] = 13
        except osv.except_osv as e:
            if vals["is_company"] == False:
                pass
            else:
                raise e
        except RedisError:
            pass

        new_id = super(res_partner, self).create(cr, uid, vals, context=context)
        partner = self.browse(cr, uid, new_id, context=context)

        self._fields_sync(cr, uid, partner, vals, context)
        self._handle_first_contact_creation(cr, uid, partner, context)
        return new_id
