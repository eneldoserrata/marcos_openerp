# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class account_fiscal_position_template(osv.osv):

    _inherit = 'account.fiscal.position.template'

    def _get_fiscal_type(self, cursor, user_id, context=None):
        return (
            ("fiscal", u"Facturas que Generan Crédito y Sustentan Costos y/o Gastos"),
            ("final", u"Facturas para Consumidores Finales"),
            ("final_note", u"Nota de crédito a consumidor final"),
            ("fiscal_note", u"Nota de crédito con derecho a crédito fiscal"),
            ("special", u"Regímenes Especiales de Tributación"),
            ("gov", u"Comprobantes Gubernamentales"),
            ("informal", u"Proveedores Informales"),
            ("minor", u"Gastos Menores"),
            ('01', u'01 - Gastos de personal'),
            ('02', u'02 - Gastos por trabajo, suministros y servicios'),
            ('03', u'03 - Arrendamientos'),
            ('04', u'04 - Gastos de Activos Fijos'),
            ('05', u'05 - Gastos de Representación'),
            ('06', u'06 - Otras Deducciones Admitidas'),
            ('07', u'07 - Gastos Financieros'),
            ('08', u'08 - Gastos Extraordinarios'),
            ('09', u'09 - Compras y Gastos que forman parte del Costo de Venta'),
            ('10', u'10 - Adquisiciones de Activos'),
            ('11', u'11 - Gastos de Seguro')
        )

    _columns = {
        "fiscal_type": fields.selection(_get_fiscal_type, "Tipo de NCF"),
        "for_supplier": fields.boolean("Para proveedores")
    }

    def generate_fiscal_position(self, cr, uid, chart_temp_id, tax_template_ref, acc_template_ref, company_id, context=None):
        """
        This method generate Fiscal Position, Fiscal Position Accounts and Fiscal Position Taxes from templates.

        :param chart_temp_id: Chart Template Id.
        :param taxes_ids: Taxes templates reference for generating account.fiscal.position.tax.
        :param acc_template_ref: Account templates reference for generating account.fiscal.position.account.
        :param company_id: company_id selected from wizard.multi.charts.accounts.
        :returns: True
        """
        if context is None:
            context = {}
        obj_tax_fp = self.pool.get('account.fiscal.position.tax')
        obj_ac_fp = self.pool.get('account.fiscal.position.account')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        fp_ids = self.search(cr, uid, [('chart_template_id', '=', chart_temp_id)])
        for position in self.browse(cr, uid, fp_ids, context=context):
            new_fp = obj_fiscal_position.create(cr, uid, {'company_id': company_id,
                                                          'name': position.name,
                                                          'note': position.note,
                                                          'fiscal_type': position.fiscal_type,
                                                          'for_supplier': position.for_supplier})
            for tax in position.tax_ids:
                obj_tax_fp.create(cr, uid, {
                    'tax_src_id': tax_template_ref[tax.tax_src_id.id],
                    'tax_dest_id': tax.tax_dest_id and tax_template_ref[tax.tax_dest_id.id] or False,
                    'position_id': new_fp
                })
            for acc in position.account_ids:
                obj_ac_fp.create(cr, uid, {
                    'account_src_id': acc_template_ref[acc.account_src_id.id],
                    'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                    'position_id': new_fp
                })
        return True
