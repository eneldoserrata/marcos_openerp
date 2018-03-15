openerp.marcos_ncf = function(instance) {
    var module = instance.point_of_sale;
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.marcos_ncf = {}

    instance.marcos_ncf.CreditButton = instance.web.Widget.extend({
        template: 'credit_order_button_template',
        init: function(options) {
            var self = this;
            this.options = options;
            this._super();
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.$el.click(function(){
                new
                self.create_bill_credit(self.options)
            });
        },
        create_bill_credit: function(options) {
            var self = this;
            options = options || {};

            var iface_print_via_proxy = pos.iface_print_via_proxy
            var printer_host = pos.iface_printer_host;
            var printer_model = pos.iface_printer_model;
            var print_receipt = pos.proxy.print_receipt
            var currentOrder = pos.get('selectedOrder');

            currentOrderLines = currentOrder.get('orderLines');
            orderLines = [];
            (currentOrderLines).each(_.bind( function(item) {
                return orderLines.push(item.export_as_JSON());
            }, this));

            customer_id = currentOrder.get_client_id() || '';

            if (orderLines.length === 0) {
                return alert('Ningún producto seleccionado!');
            };

            if (!customer_id) {
                alert('Para facturar a credito debe seleccionar el cliente!');
                $("#customer_link").click();
                return
            };

            new instance.web.Model('sale.order').call('create_sales_order', [orderLines, customer_id], {context: {type: "bill_credit", "shop_id": pos.shop_id}})
                .then(function(result){
                    if (result) {
                        if(iface_print_via_proxy){
                                var ncf = result[1];
                                var rnc = (result[2] === false ? null : result[2]);  //result[2];
                                var fiscal_type = result[3];
                                var client = result[4];
                                var branch = result[5];
                                var uid = result[6];
                                var ncf_reference = result[7];
                                print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, ncf_reference, "");
                        }else{
                            var invoice_id = result[0];
                            // this method call pdf to print
                            options.do_action('account.account_invoices',{additional_context:{active_ids:[invoice_id]}});
                        };

                        selectedOrder.destroy();
                    }
                    else {
                        return alert('Ocurrio un error miestras se creaba la cotización !');
                    };
                });
        }

    });

    instance.marcos_ncf.DraftButton = instance.web.Widget.extend({
        template: 'draft_order_button_template',
        init: function(options) {
            self = this;
            this.options = options;
            this._super();
        },
        renderElement: function(){
            var self = this;
            this._super();
            this.$el.click(function(){
                new self.create_draft_order(self.options)
            });
        },
        create_draft_order: function(options) {
            var self = this;
            this.options = options;
            var iface_print_via_proxy = pos.iface_print_via_proxy
            var print_receipt = pos.proxy.print_receipt
            var printer_host = pos.iface_printer_host;
            var printer_model = pos.iface_printer_model;
            var default_partner = false;

            show_controls = function(ret_o_id){
                if (ret_o_id != null) {
                    $(".header-cell").show();
                    $(".selection-area").show()
                    $("#orders").show()
                    $(".neworder-button").show()
                    $(".number-char").show();
                    $('*[data-mode="quantity"]').show();
                    $('*[data-mode="discount"]').show();
                    $('*[data-mode="price"]').show();
                    $('#numpad-minus').show();
                    document.getElementById("refound_label").remove();
                    $("span#sale_mode").click();
                };
            };

            currentOrder = options.pos.get('selectedOrder');

            currentOrderLines = selectedOrder.get('orderLines');
            if (currentOrderLines.length === 0) {
                return alert('Ningún producto seleccionado!');
            };

            default_partner_id = options.pos.get('shop').default_partner_id[0]
            if (!default_partner_id) {
                return alert("Se debe configurar un cliente como predeterminado para las tiendas");
            };

            if (currentOrder.get_client_id() === null) {
                currentOrder.set_client_id(default_partner_id);
                default_partner = true;
            } else if (currentOrder.get("ret_o_id")){
                default_partner = false;
            } else if (currentOrder.get_client_id() === default_partner_id){
                default_partner = true;
            };

            if (default_partner) {
                this.dialog = new instance.web.Dialog(this, {
                    title: _t("Nombre del cliente a caja"),
                    width: 320,
                    height: 180,
                    buttons: [
                        {text: "Enviar",
                        click: function(){
                            var client_name = self.dialog.$el.find("input#pos_customer_name").val();
                            client_name = jQuery.trim(client_name);
                            if (client_name.length > 0) {
                                if (!iface_print_via_proxy) {
                                    var order = currentOrder.exportAsJSON();
                                    order.temp_name = client_name;
                                    order.default_partner = true;
                                    new instance.web.Model('pos.order').call('create_draft_from_ui',[order],undefined,{shadow: true});

                                    show_controls(currentOrder.get("ret_o_id"));
                                    currentOrder.destroy();
                                    $(this).dialog('destroy');
                                    pos.set({ selectedOrder: pos.get('orders').last() });
                                } else {
                                    var order = currentOrder.exportAsJSON();
                                    order.temp_name = client_name;
                                    order.default_partner = true;
                                    new instance.web.Model('pos.order').call('create_draft_from_ui',[order],undefined,{shadow: true});
                                    print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, null, null, null, null, null, null, null, null);

                                    show_controls(currentOrder.get("ret_o_id"));

                                    currentOrder.destroy();
                                    $(this).dialog('destroy');
                                    pos.set({ selectedOrder: pos.get('orders').last() });
                                }
                            } else {
                                alert("Debe colocar un nombre o seleccionar un cliente existe")
                            }
                        }},
                        {text: "Cerrar",
                        click: function(){
                            $(this).dialog('destroy');
                        }}
                    ]
                }).open()
                this.dialog.$el.html(QWeb.render("pos-assign_name", self));
                this.dialog.$el.find("input#pos_customer_name").focus();
            } else {
                if (!iface_print_via_proxy) {
                    var order = currentOrder.exportAsJSON();
                    new instance.web.Model('pos.order').call('create_draft_from_ui',[order],undefined,{shadow: true});

                    show_controls(currentOrder.get("ret_o_id"));

                    currentOrder.destroy();
                    pos.set({ selectedOrder: pos.get('orders').last() });
                } else {
                    var order = currentOrder.exportAsJSON();
                    new instance.web.Model('pos.order').call('create_draft_from_ui',[order],undefined,{shadow: true});
                    print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, null, null, null, null, null, null, null, null);

                    show_controls(currentOrder.get("ret_o_id"));

                    currentOrder.destroy();
                    pos.set({ selectedOrder: pos.get('orders').last() });
                };
            };
        }
    });


    module.PaypadWidget = module.PosBaseWidget.extend({
        template: 'PaypadWidget',
        renderElement: function() {
            var self = this;
            this._super();
            if (self.pos.payment_pos) {
                var button = new instance.marcos_ncf.DraftButton(self);
                button.appendTo(self.$el);
            } else {
                this.pos.get('cashRegisters').each(function(cashRegister) {
                    var button = new module.PaypadButtonWidget(self,{
                        pos: self.pos,
                        pos_widget : self.pos_widget,
                        cashRegister: cashRegister
                    });
                    button.appendTo(self.$el);
                });
            };

            if (self.pos.bill_credit === true) {
                var button = new instance.marcos_ncf.CreditButton(self)
                button.appendTo(self.$el);
            };

        }
    });

    module.PosWidget = module.PosWidget.extend({
        start: function() {
            var self = this;
            return self.pos.ready.done(function() {
                self.build_currency_template();
                self.renderElement();

                self.$('.neworder-button').click(function(){
                    self.pos.add_new_order();
                });

                self.$('.removeorder-button').click(function(){
                    if (self.pos.get("selectedOrder").get("ret_o_id") != null) {
                        $(".header-cell").show();
                        $(".selection-area").show()
                        $("#orders").show()
                        $(".neworder-button").show()
                        $(".number-char").show();
                        $('*[data-mode="quantity"]').show();
                        $('*[data-mode="discount"]').show();
                        $('*[data-mode="price"]').show();
                        $('#numpad-minus').show();
                        document.getElementById("refound_label").remove();
                        $("span#sale_mode").click();
                    };
                    self.pos.get('selectedOrder').destroy();
                    self.pos.set({ selectedOrder: self.pos.get('orders').last() });
                });

                //when a new order is created, add an order button widget
                self.pos.get('orders').bind('add', function(new_order){
                    var new_order_button = new module.OrderButtonWidget(null, {
                        order: new_order,
                        pos: self.pos
                    });
                    new_order_button.appendTo($('#orders'));
                    new_order_button.selectOrder();
                }, self);

                self.pos.get('orders').add(new module.Order({ pos: self.pos }));

                self.build_widgets();

                self.screen_selector.set_default_screen();

                window.screen_selector = self.screen_selector;

                self.pos.barcode_reader.connect();

                instance.webclient.set_content_full_screen(true);

                if (!self.pos.get('pos_session')) {
                    self.screen_selector.show_popup('error', 'Sorry, we could not create a user session');
                }else if(!self.pos.get('pos_config')){
                    self.screen_selector.show_popup('error', 'Sorry, we could not find any PoS Configuration for this session');
                }

                instance.web.unblockUI();
                self.$('.loader').animate({opacity:0},1500,'swing',function(){self.$('.loader').hide();});

                self.pos.flush();

            }).fail(function(){   // error when loading models data from the backend
                instance.web.unblockUI();
                return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_pos_session_opening']], ['res_id'])
                    .pipe( _.bind(function(res){
                        return instance.session.rpc('/web/action/load', {'action_id': res[0]['res_id']})
                            .pipe(_.bind(function(result){
                                var action = result.result;
                                this.do_action(action);
                            }, this));
                    }, self));
            });
        }
    });

    module.ProxyDevice  = module.ProxyDevice.extend({
        init: function(options){
            this._super.apply(this, arguments);
            self = this;
        },
        set_printed: function(response, oid){
            if (response==="success") {
                new instance.web.Model("pos.order").call("set_printed", [oid]);
                $("span#sale_mode").click();
            };

        },
        print_receipt: function(receipt, printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, ncf_reference, oid, comments){
            console.log("invoice recived")
            var data = {
                receipt: receipt,
                brand: printer_model,
                ncf: ncf,
                rnc: rnc,
                fiscal_type: fiscal_type,
                client: client,
                branch: branch,
                uid: uid,
                ncf_reference: ncf_reference,
                oid: oid,
                comment: comments
            };


    /*

            $.ajax({

                type: 'POST',
                url: printer_host,
                data: JSON.stringify(data),
                dataType:'json',
                success: function(response) {
                    self.set_printed(response, data.oid);
                }
            });

    */
            $.ajax({
                type: 'GET',
                url: printer_host,
                data: data,
                dataType:'jsonp',
//                jsonp:false,
                jsonpCallback: "ipf",
//                crossDomain: true,
                success: function(response) {

                    self.set_printed(response.status, data.oid);
                }
            });
        }
    });

    module.PosModel = module.PosModel.extend({
        load_server_data: function(){
            var self = this;
            var loaded = self.fetch('res.users',['name','company_id'],[['id','=',this.session.uid]])
                .then(function(users){
                    self.set('user',users[0]);
                    return self.fetch('res.company',
                    [
                        'currency_id',
                        'email',
                        'website',
                        'company_registry',
                        'vat',
                        'name',
                        'phone',
                        'partner_id'
                    ],
                    [['id','=',users[0].company_id[0]]]);
                }).then(function(companies){
                    self.set('company',companies[0]);

                    return self.fetch('res.partner',['contact_address'],[['id','=',companies[0].partner_id[0]]]);
                }).then(function(company_partners){
                    self.get('company').contact_address = company_partners[0].contact_address;

                    return self.fetch('product.uom', null, null);
                }).then(function(units){
                    self.set('units',units);
                    var units_by_id = {};
                    for(var i = 0, len = units.length; i < len; i++){
                        units_by_id[units[i].id] = units[i];
                    }
                    self.set('units_by_id',units_by_id);

                    return self.fetch('product.packaging', null, null);
                }).then(function(packagings){
                    self.set('product.packaging',packagings);

                    return self.fetch('res.users', ['name','ean13'], [['ean13', '!=', false]]);
                }).then(function(users){
                    self.set('user_list',users);

                    return self.fetch('res.partner', ['name','ean13'], [['ean13', '!=', false]]);
                }).then(function(partners){
                    self.set('partner_list',partners);

                    return self.fetch('account.tax', ['amount', 'price_include', 'type', 'exempt']);
                }).then(function(taxes){
                    self.set('taxes', taxes);

                    return self.fetch(
                        'pos.session',
                        ['id', 'journal_ids','name','user_id','config_id','start_at','stop_at'],
                        [['state', '=', 'opened'], ['user_id', '=', self.session.uid]]
                    );
                }).then(function(sessions){
                    self.set('pos_session', sessions[0]);

                    return self.fetch(
                        'pos.config',
                        ['name','journal_ids','shop_id','journal_id',
                         'iface_self_checkout', 'iface_led', 'iface_cashdrawer',
                         'iface_payment_terminal', 'iface_electronic_scale', 'iface_barscan', 'iface_vkeyboard',
                         'iface_print_via_proxy','iface_cashdrawer','state','sequence_id','session_ids',
                         'iface_printer_host', 'iface_printer_model',
                         'not_show_zero_stock', 'live_search', 'bill_credit', 'payment_pos'], // by eneldo select two nwe field
                        [['id','=', self.get('pos_session').config_id[0]]]
                    );
                }).then(function(configs){
                    var pos_config = configs[0];
                    self.set('pos_config', pos_config);

                    self.iface_electronic_scale    =  !!pos_config.iface_electronic_scale;
                    self.iface_print_via_proxy     =  !!pos_config.iface_print_via_proxy;

                    self.iface_printer_host        =  pos_config.iface_printer_host; // by eneldo set the new seleted field
                    self.iface_printer_model       =  pos_config.iface_printer_model;

                    self.iface_vkeyboard           =  !!pos_config.iface_vkeyboard;
                    self.iface_self_checkout       =  !!pos_config.iface_self_checkout;
                    self.iface_cashdrawer          =  !!pos_config.iface_cashdrawer;

                    self.bill_credit               =  pos_config.bill_credit;
                    self.shop_id                   =  pos_config.shop_id[0]
                    self.payment_pos               =  pos_config.payment_pos

                    return self.fetch('sale.shop',[],[['id','=',pos_config.shop_id[0]]]);
                }).then(function(shops){
                    self.set('shop',shops[0]);

                    return self.fetch('product.pricelist',['currency_id'],[['id','=',self.get('shop').pricelist_id[0]]]);
                }).then(function(pricelists){
                    self.set('pricelist',pricelists[0]);

                    return self.fetch('res.currency',['symbol','position','rounding','accuracy'],[['id','=',self.get('pricelist').currency_id[0]]]);
                }).then(function(currencies){
                    self.set('currency',currencies[0]);

                    return self.fetch('product.packaging',['ean','product_id']);
                }).then(function(packagings){
                    self.db.add_packagings(packagings);

                    return self.fetch('pos.category', ['id','name','parent_id','child_id','image'])
                }).then(function(categories){
                    self.db.add_categories(categories);

                    return self.fetch(
                        'product.product',
                         ['name', 'list_price','price','pos_categ_id', 'taxes_id', 'ean13', 'qty_available',
                         'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description'],
                        [['sale_ok','=',true],['available_in_pos','=',true]],
                        {pricelist: self.get('shop').pricelist_id[0], 'qty_exists': self.get("pos_config").not_show_zero_stock} // context for price
                    );
                }).then(function(products){
                    self.db.add_products(products);

                    return self.fetch(
                        'account.bank.statement',
                        ['account_id','currency','journal_id','state','name','user_id','pos_session_id'],
                        [['state','=','open'],['pos_session_id', '=', self.get('pos_session').id]]
                    );
                }).then(function(bank_statements){
                    var journals = new Array();
                    _.each(bank_statements,function(statement) {
                        journals.push(statement.journal_id[0])
                    });
                    self.set('bank_statements', bank_statements.reverse());

                    return self.fetch('account.journal', undefined, [['id','in', journals]]);
                }).then(function(journals){
                    self.set('journals',journals);

                    // associate the bank statements with their journals.
                    var bank_statements = self.get('bank_statements');
                    for(var i = 0, ilen = bank_statements.length; i < ilen; i++){
                        for(var j = 0, jlen = journals.length; j < jlen; j++){
                            if(bank_statements[i].journal_id[0] === journals[j].id){
                                bank_statements[i].journal = journals[j];
                                bank_statements[i].self_checkout_payment_method = journals[j].self_checkout_payment_method;
                            }
                        }
                    }
                    self.set({'cashRegisters' : new module.CashRegisterCollection(self.get('bank_statements'))});

                });

            return loaded;
    }
});


    module.PaymentScreenWidget = module.PaymentScreenWidget.extend({

        validateCurrentOrder: function(options) {
            var self = this;
            this.db = new instance.point_of_sale.PosLS();
            options = options || {};

            var iface_print_via_proxy = this.pos.iface_print_via_proxy
            var printer_host = this.pos.iface_printer_host;
            var printer_model = this.pos.iface_printer_model;
            var print_receipt = this.pos.proxy.print_receipt

            var currentOrder = this.pos.get('selectedOrder');
            if (currentOrder.get_client_id() === null) {
                currentOrder.set_client_id(self.pos.get('shop').default_partner_id[0])
            }
            client_id = currentOrder.get_client_id();

            show_controls = function(ret_o_id){
                if (ret_o_id != null) {
                    $(".header-cell").show();
                    $(".selection-area").show()
                    $("#orders").show()
                    $(".neworder-button").show()
                    $(".number-char").show();
                    $('*[data-mode="quantity"]').show();
                    $('*[data-mode="discount"]').show();
                    $('*[data-mode="price"]').show();
                    $('#numpad-minus').show();
                    if (document.getElementById("refound_label")){
                        document.getElementById("refound_label").remove();
                    };
                    $("span#sale_mode").click();
                };
            };


            if(options.invoice){
                if (client_id == null) {
                    alert('No se a selecciona ningun Cliente para poder editarlo!');
                    return;
                }
                var order = currentOrder.exportAsJSON();
                if (order.amount_total === 0){
                    return alert("No puede grabar una factura con valor cero!");
                };
                // deactivate the validation button while we try to send the order
                this.pos_widget.action_bar.set_button_disabled('validation',true);
                this.pos_widget.action_bar.set_button_disabled('invoice',true);
                this.db.add_order(order);
                last_order = this.db.get_orders();
                var rpc = new instance.web.Model('pos.order').call('create_from_ui',[[last_order[0]]],undefined,{shadow: true});
                rpc.done(function(){
                    self.db.remove_order(last_order[0].id);
                    self.set('nbr_pending_operations',self.db.get_orders().length);
                });

                var invoice_id = null;

                rpc.pipe(function(oid) {
                    if (oid) {
                        new instance.web.Model("pos.order").get_func("action_create_invoice")([parseInt(oid)]).pipe(
                        function(result) {

                            if(iface_print_via_proxy){
                                var ncf = result[1];
                                var rnc = (result[2] === false ? null : result[2]);  //result[2];
                                var fiscal_type = result[3];
                                var client = result[4];
                                var branch = result[5];
                                var uid = result[6];
                                var ncf_reference = result[7];
                                var pos_name = "Ref: "+result[9]
//                                print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, ncf_reference, oid, "Esta factura tiene una oferta");
                                print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, ncf_reference, oid, pos_name);
                            }else{
                                var invoice_id = result[0];
                                // this method call pdf to print
                                self.pos_widget.do_action('account.account_invoices',{additional_context:{active_ids:[invoice_id]}});
                            };

                            if (result[8] === true){
                                alert('URGENTE! Cantidad de secuencias NCF disponibles se aproxima a su fin. Favor notificar al encargado(a) de contabilidad.');
                            }
                        });
                    }
                    show_controls(currentOrder.get("ret_o_id"));
                    self.pos_widget.action_bar.set_button_disabled('validation',false);
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    currentOrder.destroy();
                    self.pos.set({ selectedOrder: pos.get('orders').last() });
                });
            } else {
                this.pos.push_order(currentOrder.exportAsJSON())
                if(this.pos.iface_print_via_proxy){
                    this.pos.proxy.print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, null, null, null);
                    this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                    $("span#sale_mode").click();
                }else{
                    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                    $("span#sale_mode").click();
                }
            }
        }

    });

    instance.marcos_ncf.PrintIpfVoucher = instance.web.form.FormWidget.extend({
        template: "print_ncf",
        start: function() {
            var self = this;
            var order_name = this.field_manager.get_field_value("name");
            var order_instance = new instance.web.Model("pos.order");
            this.$el.click(function() {
                order_instance.call("print_on_ipf", [order_name], {context: new instance.web.CompoundContext()}).then(function(result) {
                    var proxy = new module.ProxyDevice()//pos.proxy.print_receipt
                    proxy.print_receipt(result.receipt, result.host, result.brand, result.ncf, result.rnc, result.fiscal_type, result.client, result.branch, result.uid, result.ncf_reference, result.oid, result.comment);
                });
            });
        }
    });

    instance.web.form.custom_widgets.add("printipf", "instance.marcos_ncf.PrintIpfVoucher");
};
