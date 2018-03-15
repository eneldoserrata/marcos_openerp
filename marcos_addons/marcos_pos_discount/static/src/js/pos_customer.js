openerp.marcos_pos_discount = function (instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.point_of_sale.ProductScreenWidget = instance.point_of_sale.ProductScreenWidget.extend({
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            this._super.apply(this, arguments);
            orderView = new instance.point_of_sale.OrderWidget(this, {});
            pos = this.pos;
            selectedOrder = this.pos.get('selectedOrder');

            $("span#ok_button").click(function () {
                var self = this;
                var disc_amt = parseInt($('#disc_amount').val());
//                if (!disc_amt || disc_amt < 0) {
                if (!disc_amt) {
                    return alert("No ha especificado el descuento que desea aplicar!");
                }
                var amount_list = [];
                var discount_list = new instance.web.Model("pos.group.discount").get_func("search_read")([], ['name', 'amount', 'users']).pipe(
                    function (result) {
                        if (result) {
                            if (!result[0]) {
                                return alert("Su usuario no esta autorizado a realizar descuentos!");
                            }
                            ;
                            var max_amt_disc = 0;
                            _.each(result, _.bind(function (res) {
                                _.each(res.users, _.bind(function (user) {
                                    if (pos.get('user').id == user) {
                                        amount_list.push(res.amount);
                                    }
                                }));
                            }));

                            if (amount_list.length === 0) {
                                return alert("Usted no tiene permiso para aplicar descuentos o recargos!");
                            }
                            ;

                            if (amount_list.length > 1) {
                                max_amt_disc = _.max(amount_list);
                            } else {
                                max_amt_disc = amount_list[0]
                            }
                            if (disc_amt <= max_amt_disc) {
                                max_amt_disc = disc_amt;
                                disc_amt = disc_amt;
                            } else {
                                alert('No se puede introducir más de descuento: ' + max_amt_disc.toString());
                                $('#disc_amount').val('')
                                return true;
                            }
                            if (max_amt_disc !== 0) {
                                if (max_amt_disc > 0) {
                                    max_amt_disc = max_amt_disc.toString() + '/discount';
                                } else {
                                    max_amt_disc = max_amt_disc.toString() + '/Recargo';
                                }
                                ;

                                orderView.set_value(max_amt_disc);
                                $('#disc_amount').val('');
                                return true;
                            }
                        } else {
                            alert('Por favor introduzca descuento válido !');
                        }
                    });
            });

            $("span#reset_button").click(function () {
                orderView.set_value((0).toString() + '/discount');
            });

            $("span#precuenta").click(function () {
                var printer_host = pos.iface_printer_host;
                var printer_model = pos.iface_printer_model;
                var print_receipt = pos.proxy.print_receipt;
                selectedOrder = pos.get('selectedOrder');
                console.log(selectedOrder);
//                print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, null, null, "nofiscal", client, branch, uid, null, null, null);
                print_receipt(selectedOrder.export_for_printing(), printer_host, printer_model, "", "", "nofiscal", "", "", 1, "", "", "");
            });

        },
        close: function () {
            this._super();
            this.pos_widget.order_widget.set_numpad_state(null);
            this.pos_widget.payment_screen.set_numpad_state(null);
        }
    });

    instance.point_of_sale.OrderWidget = instance.point_of_sale.OrderWidget.extend({
        init: function (parent, options) {
            this._super(parent, options);
            this.display_mode = options.display_mode || 'numpad';   // 'maximized' | 'actionbar' | 'numpad'
            this.set_numpad_state(options.numpadState);
            this.pos.bind('change:selectedOrder', this.change_selected_order, this);
            this.bind_orderline_events();
            this.orderlinewidgets = [];
        },
        set_value: function (val) {
            var order = this.pos.get('selectedOrder');
            try {
                var prod_id = order.getSelectedLine().get_product().get('id');
            } catch (err) {
                return alert("No ha seleccionado ningun producto");
            }
            ;
            if (val.indexOf('/') != -1 && order.get('orderLines').length !== 0) {
                discount_vals = val.split('/');
                val = discount_vals[0];
                order.getSelectedLine().set_discount(val);

                //  Discount for all products in Order List.
                this.currentOrderLines.each(_.bind(function (orderLine) {
                    orderLine.set_discount(val);
                }));
            } else if (order.get('orderLines').length !== 0) {
                var mode = this.numpadState.get('mode');
                if (mode === 'quantity') {
                    var ret_o_id = order.get_ret_o_id();
                    if (ret_o_id && ret_o_id.toString() != 'Missing Receipt') {
                        var self = this;
                        var pids = [];
                        new instance.web.Model("pos.order.line").get_func("search_read")
                        ([
                                ['order_id', '=', ret_o_id],
                                ['product_id', '=', prod_id],
                                ['return_qty', '>', 0]
                            ],
                            ['return_qty', 'id']).pipe(
                            function (result) {
                                if (result && result.length > 0) {
                                    if (result[0].return_qty > 0) {
                                        add_prod = true;
                                        (order.get('orderLines')).each(_.bind(function (item) {
                                            if (prod_id == item.get_product().get('id') &&
                                                result[0].return_qty < parseFloat(val)) {
                                                var error_str = _t('Can not return more products !');
                                                var error_dialog = new instance.web.Dialog(this, {
                                                    width: '300',
                                                    buttons: [
                                                        {text: _t("Close"), click: function () {
                                                            $(this).dialog('destroy');
                                                        }}
                                                    ]
                                                }).open();
                                                error_dialog.$el.append(
                                                        '<span id="error_str" style="font-size:18px;">' + error_str + '</span>');
                                                add_prod = false;
                                            }
                                        }));
                                    }
                                    if (add_prod) {
                                        var partner_id = parseInt(order.get_client_id());
                                        var pricelist_id = parseInt(order.get_pricelist());
                                        if ((val != 'remove') && pricelist_id && order && order.getSelectedLine().get_product().id) {
                                            var p_id = order.getSelectedLine().get_product().id;
                                            if (!val) {
                                                val = 1;
                                            }
                                            new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], p_id, val).pipe(
                                                function (res) {
                                                    if (res[pricelist_id]) {
                                                        pricelist_value = parseFloat(res[pricelist_id].toFixed(2));
                                                        if (pricelist_value && order.getSelectedLine()) {
                                                            order.getSelectedLine().set_quantity(val);
                                                            order.getSelectedLine().set_unit_price(pricelist_value);
                                                        }
                                                    }
                                                }
                                            );
                                        } else {
                                            order.getSelectedLine().set_quantity(val);
                                        }
                                    }
                                }
                            }
                        );
                    } else {
                        var partner_id = parseInt(order.get_client_id());
                        var pricelist_id = parseInt(order.get_pricelist());
                        if ((val != 'remove') && pricelist_id && order && order.getSelectedLine().get_product().id) {
                            var p_id = order.getSelectedLine().get_product().id;
                            if (!val) {
                                val = 1;
                            }
                            new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], p_id, val).pipe(
                                function (res) {
                                    if (res[pricelist_id]) {
                                        pricelist_value = parseFloat(res[pricelist_id].toFixed(2));
                                        if (pricelist_value && order.getSelectedLine()) {
                                            order.getSelectedLine().set_quantity(val);
                                            order.getSelectedLine().set_unit_price(pricelist_value);
                                        }
                                    }
                                }
                            );
                        } else {
                            order.getSelectedLine().set_quantity(val);
                        }
                    }
                } else if (mode === 'discount') {
                    order.getSelectedLine().set_discount(val)
                    var amount_list = [];
                    var max_amt_disc = 0;
                    var disc_amt = order.getSelectedLine().discount;
                    var discount_list = new instance.web.Model("pos.group.discount").get_func("search_read")([], ['name', 'amount', 'users']).pipe(
                        function (result) {
                            if (result) {
                                _.each(result, _.bind(function (res) {
                                    _.each(res.users, _.bind(function (user) {
                                        if (pos.get('user').id == user) {
                                            amount_list.push(res.amount);
                                        }
                                    }));
                                }));
                                this.numpad_state = new instance.point_of_sale.NumpadState();
                                if (amount_list.length > 1) {
                                    max_amt_disc = _.max(amount_list);
                                } else {
                                    max_amt_disc = amount_list[0]
                                }
                                if (disc_amt <= max_amt_disc) {
                                    max_amt_disc = disc_amt;
                                    disc_amt = disc_amt;
                                } else {
                                    if (max_amt_disc) {
                                        alert('No se puede introducir más de descuento: ' + max_amt_disc.toString());
                                    } else {
                                        alert('Por favor, especifique el límite de descuento primero.')
                                        return false;
                                    }
                                    //max_amt_disc = 0;
                                }
                                order.getSelectedLine().set_discount(max_amt_disc);
                            } else {
                                alert('Por favor introduzca descuento válido!');
                            }
                        });
                } else if (mode === 'price') {
                    order.getSelectedLine().set_unit_price(val);
                }
            } else {
                this.pos.get('selectedOrder').destroy();
            }
        }
    });
}