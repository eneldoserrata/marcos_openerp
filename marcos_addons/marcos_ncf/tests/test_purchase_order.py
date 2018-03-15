# -*- encoding: utf-8 -*-
from openerp.tests import common

# Assign ID for partners to test.
# TODO create partners in test
PARTNER_ID = 30059
PARTNER_ID_USD = 30027

class TestPurchaseOrder(common.TransactionCase):
    def setUp(self):
        super(TestPurchaseOrder, self).setUp()

        # Cursor and user initialization
        cr, uid = self.cr, self.uid

        # Modules to test
        self.product_product_obj = self.registry('product.product')
        self.purchase_order_obj = self.registry('purchase.order')
        self.purchase_order_line_obj = self.registry('purchase.order.line')
        self.purchase_config_settings_obj = self.registry('purchase.config.settings')

        # Get group_costing_method for validation
        self.group_costing_method = False
        purchase_settings_ids = self.purchase_config_settings_obj.search(cr, uid, [], order='id desc')
        if purchase_settings_ids:
            self.group_costing_method = self.purchase_config_settings_obj.\
                    read(cr, uid, purchase_settings_ids[0], ['group_costing_method'])['group_costing_method']

        # Set values to test
        self.original_price = 9.5
        self.changed_price = 8.3

        # Create product.
        values = {'name': 'Producto #1',
                'standard_price': self.original_price
                }
        self.product_id = self.product_product_obj.create(cr, uid, values)
        product_id = self.product_id
        self.product_obj = self.product_product_obj.browse(cr, uid, product_id)

    def testUnitToUnit(self):
        """
        Change the price_unit of a purchase.order.line with UOM = Unit.
        (Product has UOM = Unit)

        porder = purchase_order

        """

        cr, uid = self.cr, self.uid

        # Create purchase.order
        partner_values = self.purchase_order_obj.onchange_partner_id(cr, uid, 0, PARTNER_ID)['value']
        values = {'partner_id': PARTNER_ID,
                  'pricelist_id': partner_values.get('pricelist_id', False),
                  'fiscal_position': partner_values.get('fiscal_position', False),
                  'payment_term_id': partner_values.get('payment_term_id', False),
                  'invoice_method': partner_values.get('invoice_method', False),
                  'location_id': 1,  # TODO get proper location_id
                  }
        porder_id = self.purchase_order_obj.create(cr, uid, values)
        porder_obj = self.purchase_order_obj.browse(cr, uid, porder_id)

        # Create purchase.order.line
        value = self.purchase_order_line_obj.onchange_product_uom(cr, uid, 0,
                        porder_obj.pricelist_id.id, self.product_id, 1, self.product_obj.uom_po_id.id, porder_obj.partner_id.id,
                        date_order=porder_obj.date_order, fiscal_position_id=porder_obj.fiscal_position.id)
                        # date_planned=False, name=product_obj.name, price_unit=False, context=None)
        values = value['value']
        values.update({'order_id': porder_id,
                       'product_id': self.product_id,
                       'price_unit': self.changed_price,
                       })
        self.purchase_order_line_obj.create(cr, uid, values)

        # Confirm order
        self.purchase_order_obj.wkf_confirm_order(cr, uid, [porder_id])

        product_obj = self.product_product_obj.browse(cr, uid, self.product_id)

        # If group_costing_method is activated, price shouldn't be udpated.
        if self.group_costing_method:
            self.assertEqual(product_obj.standard_price, self.original_price)
        else:
            self.assertEqual(product_obj.standard_price, self.changed_price)

    def testUnitToDozen(self):
        """
        Change the price_unit and UOM of a purchase.order.line (UOM to Dozen = Unit * 12).
        (Product has UOM = Unit)

        porder = purchase_order

        """

        cr, uid = self.cr, self.uid

        # Create purchase.order
        partner_values = self.purchase_order_obj.onchange_partner_id(cr, uid, 0, PARTNER_ID)['value']
        values = {'partner_id': PARTNER_ID,
                  'pricelist_id': partner_values.get('pricelist_id', False),
                  'fiscal_position': partner_values.get('fiscal_position', False),
                  'payment_term_id': partner_values.get('payment_term_id', False),
                  'invoice_method': partner_values.get('invoice_method', False),
                  'location_id': 1,  # TODO get proper location_id
                  }
        porder_id = self.purchase_order_obj.create(cr, uid, values)
        porder_obj = self.purchase_order_obj.browse(cr, uid, porder_id)

        # Get product_uom object: Dozen for this test (Unit * 12).
        uom = self.registry('product.uom').browse(cr, uid, 2)

        # Create purchase.order.line
        values = {}
        onchange_values = self.purchase_order_line_obj.onchange_product_uom(cr, uid, 0,
                                        porder_obj.pricelist_id.id, self.product_id, 1, uom.id,  
                                        porder_obj.partner_id.id, date_order=porder_obj.date_order,
                                        fiscal_position_id=porder_obj.fiscal_position.id)
                                        # date_planned=False, name=product_obj.name, price_unit=False, context=None)
        values = onchange_values['value']
        values.update({'order_id': porder_id,
                       'product_id': self.product_id,
                       'price_unit': self.changed_price / uom.factor,
                       })
        self.purchase_order_line_obj.create(cr, uid, values)

        # Confirm order
        self.purchase_order_obj.wkf_confirm_order(cr, uid, [porder_id])

        product_obj = self.product_product_obj.browse(cr, uid, self.product_id)
        # If group_costing_method is activated, price shouldn't be udpated.
        if self.group_costing_method:
            self.assertEqual(product_obj.standard_price, self.original_price)
        else:
            self.assertEqual(product_obj.standard_price, self.changed_price)

    def testCurrencyChange(self):
        """
        Update product cost when purchasing with
        a different currency than the base one,

        porder = purchase_order

        """

        cr, uid = self.cr, self.uid

        # Create purchase.order
        partner_values = self.purchase_order_obj.onchange_partner_id(cr, uid, 0, PARTNER_ID_USD)['value']
        values = {'partner_id': PARTNER_ID_USD,
                  'pricelist_id': partner_values.get('pricelist_id', False),
                  'fiscal_position': partner_values.get('fiscal_position', False),
                  'payment_term_id': partner_values.get('payment_term_id', False),
                  'invoice_method': partner_values.get('invoice_method', False),
                  'location_id': 1,  # TODO get proper location_id
                  }
        porder_id = self.purchase_order_obj.create(cr, uid, values)
        porder_obj = self.purchase_order_obj.browse(cr, uid, porder_id)

        # Get product_uom object: Dozen for this test (Unit * 12).
        uom = self.registry('product.uom').browse(cr, uid, 2)

        # Create purchase.order.line
        values = {}
        onchange_values = self.purchase_order_line_obj.onchange_product_uom(cr, uid, 0,
                                        porder_obj.pricelist_id.id, self.product_id, 1, uom.id,  
                                        porder_obj.partner_id.id, date_order=porder_obj.date_order,
                                        fiscal_position_id=porder_obj.fiscal_position.id)
                                        # date_planned=False, name=product_obj.name, price_unit=False, context=None)
        values = onchange_values['value']
        values.update({'order_id': porder_id,
                       'product_id': self.product_id,
                       'price_unit': self.changed_price / uom.factor,
                       })
        self.purchase_order_line_obj.create(cr, uid, values)

        # Confirm order
        self.purchase_order_obj.wkf_confirm_order(cr, uid, [porder_id])

        product_obj = self.product_product_obj.browse(cr, uid, self.product_id)
        # If group_costing_method is activated, price shouldn't be udpated.
        if self.group_costing_method:
            self.assertEqual(product_obj.standard_price, self.original_price)
        else:
            self.assertEqual(product_obj.standard_price, self.changed_price)
