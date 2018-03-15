openerp.marcos_pos_ncf = function(instance) {
    var module = instance.point_of_sale;
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.marcos_pos_ncf = {}

    module.ProductWidget = module.PosBaseWidget.extend({
        template: 'ProductWidget',
        init: function(parent, options) {
            this._super(parent,options);
            this.model = options.model;
            this.model.attributes.weight = options.weight;
            this.next_screen = options.next_screen; //when a product is clicked, this screen is set
            this.click_product_action = options.click_product_action;
        },
        // returns the url of the product thumbnail
        renderElement: function() {
            this._super();
            this.$('img').replaceWith(this.pos_widget.image_cache.get_image(this.model.get_image_url()));
            var self = this;
            $("a", this.$el).click(function(e){
                $('.searchbox input').val('').focus();
                if(self.click_product_action){
                    self.click_product_action(self.model);
                }
            });
        },
    });

    module.ProxyDevice  = module.ProxyDevice.extend({
        init: function(options){
            this._super.apply(this, arguments);
            self = this;
        },
        print_receipt: function(receipt, printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, oid){
            var data = {
                receipt: receipt,
                brand: printer_model,
                ncf: ncf,
                rnc: rnc,
                fiscal_type: fiscal_type,
                client: client,
                branch: branch,
                uid: uid,
                oid: oid
            };

            $.ajax({
               //type: 'POST',
                url: "http://"+printer_host,
                data: data,
                //async: false,
                //contentType: "application/json",
                dataType:'jsonp',
                //jsonp:'jsonp',
                //crossDomain: true,
                success: function(response) {
                    self.set_printed(response, data.oid)
                }
            });
        },
        set_printed: function(response, oid){
            if (response==="true") {
               new instance.web.Model("pos.order").call("set_printed", [oid]);
            };

        }
    });

    module.PosModel = module.PosModel.extend({
    // loads all the needed data on the sever. returns a deferred indicating when all the data has loaded.
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

                return self.fetch('account.tax', ['amount', 'price_include', 'type']);
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
                     'iface_printer_host', 'iface_printer_model'], // by eneldo select two nwe field
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

//                self.start = new Date();
                return self.fetch(
                    'product.product',
                    ['name', 'list_price','price','pos_categ_id', 'taxes_id', 'ean13', 'default_code',
                     'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description'],
                    [['sale_ok','=',true],['available_in_pos','=',true]],
                    {pricelist: self.get('shop').pricelist_id[0]} // context for price
                );
            }).then(function(products){
                self.db.add_products(products);
//                self.end = new Date();
//                self.time = self.end-self.start;
//                console.log("productos "+self.time)

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
                self.set('bank_statements', bank_statements);

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

    module.ProductScreenWidget = module.ProductScreenWidget.extend({
        init: function() {
            this._super.apply(this, arguments);
        },
        start:function(){
            this._super.apply(this, arguments);
            orderView = new module.OrderWidget(this, {});
            pos = this.pos;
            selectedOrder = this.pos.get('selectedOrder');
            if ($('button.select-order').length == 1) {
                pos = this.pos;
                $("#customer_link").click(function() {
                    selectedOrder = pos.get('selectedOrder');
                    var self = this;
                    new instance.web.Model("res.partner").get_func("search_read")(domain=[['customer', '=', true]], fields=['id'], offset=0, limit=20).pipe(
                        function(result) {
                            initial_ids = _.map(result, function(x) {return x['id']});
                            var pop = new instance.web.form.SelectCreatePopup(this);
                            pop.select_element(
                                'res.partner',
                                {
                                    title: 'Select Customer',
                                    initial_ids: initial_ids,
                                    initial_view: 'search',
                                    disable_multiple_selection: true
                                }
                        );
                        pop.on("elements_selected", self, function(element_ids) {
                            var dataset = new instance.web.DataSetStatic(self, 'res.partner', {});
                            dataset.name_get(element_ids).done(function(data) {
                                selectedOrder.set_client(data[0][1]);
                                selectedOrder.set_client_id(data[0][0]);
                                selectedOrder.set_pricelist_val(data[0][0]);
                                selectedOrder.set_fiscal_val(data[0][0]);
                            });
                        });
                    });
                });

                // Create new customer

                $("#create_link").click(function() {
                    selectedOrder = pos.get('selectedOrder');
                    var self = this;
                    new instance.web.Model("res.partner").get_func("search_read")(domain=[['customer', '=', true]], fields=['id'], offset=0, limit=20).pipe(
                        function(result) {
                            initial_ids = _.map(result, function(x) {return x['id']});
                            var create_pop = new instance.web.form.SelectCreatePopup(this);
                            create_pop.select_element(
                                'res.partner',
                                {
                                    title: 'Select Customer',
                                    initial_ids: [],
                                    initial_view: 'form',
                                    disable_multiple_selection: true
                                }
                        );
                        create_pop.on("elements_selected", self, function(element_ids) {
                            var dataset = new instance.web.DataSetStatic(self, 'res.partner', {});
                            dataset.name_get(element_ids).done(function(data) {
                                selectedOrder.set_client(data[0][1]);
                                selectedOrder.set_client_id(data[0][0]);
                            });
                        });
                    });
                });

                // Edit Customer once selected.

                $("#edit_link").click(function() {
                    selectedOrder = pos.get('selectedOrder');
                    var self = this;
                    var client_id = selectedOrder.get_client_id();
                    var client_name = selectedOrder.get_client_name();
                    if (!client_id) {
                        alert('Customer is not selected !');
                        return;
                    } else {
                        var edit_pop = new instance.web.form.FormOpenPopup(this);
                        edit_pop.show_element("res.partner", selectedOrder.get_client_id(), {}, {
                            title: _t("Edit Customer "),
                            readonly: false
                        });
                        edit_pop.on("write_completed", self, function(res) {
                            if (res) {
                                var dataset = new instance.web.DataSetStatic(self, 'res.partner', {});
                                dataset.name_get([client_id]).done(function(data) {
                                    selectedOrder.set_client(data[0][1]);
                                    selectedOrder.set_client_id(data[0][0]);
                                });
                            }
                        });
                    }
                });

                $("#create_so").click(function() {
                    selectedOrder = pos.get('selectedOrder');
                    currentOrderLines = selectedOrder.get('orderLines');
                    orderLines = [];
                    (currentOrderLines).each(_.bind( function(item) {
                        return orderLines.push(item.export_as_JSON());
                    }, this));
                    customer_id = selectedOrder.get_client_id() || '';

                    if (orderLines.length === 0) {
                        return alert('No product selected !');
                    }
                    if (!customer_id) {
                        return alert('Customer is not selected !');
                    }
                    (new instance.web.Model('sale.order')).get_func('create_sales_order')(orderLines, customer_id)
                    .pipe( _.bind(function(res){
                        if (res) {
                            return alert("Sales Order Created: " + res);
                        }
                        else {
                            return alert('Error in creating Sales Order !');
                        }
                    }, self));
                });

                // Serial Number Popup
                $("#assign_serial").click(function() {
                    var self = this;
                    var selectedOrder = pos.get('selectedOrder');
                    if (selectedOrder && selectedOrder.getSelectedLine()) {
                        var order_serial = selectedOrder.getSelectedLine().get_serial();
                    }
                    if (order_serial) {
                        this.dialog = new instance.web.Dialog(this, {
                            title: _t("Enter Serial Number"),
                            width: 320,
                            height: 180,
                            buttons: [
                                {text: _t("Validate"), click: function() {
                                    var sr_no = self.dialog.$el.find("input#pos_serial").val();
                                    sr_no = jQuery.trim(sr_no);
                                    var sel_id = selectedOrder.getSelectedLine().get_product().get('id');
                                    var old_sr = selectedOrder.getSelectedLine().get_serial();
                                    if (sr_no.length > 0) {
                                        selectedOrder.getSelectedLine().set_serial(sr_no);
                                        new instance.web.Model("stock.production.lot").get_func("search_read")
                                                ([['product_id', '=', sel_id], ['name', '=', sr_no]]).pipe(
                                        function(result) {
                                            if (result && result.length > 0) {
                                                alert('Same product is already assigned with same serial number !');
                                                sr_no = null;
                                                selectedOrder.getSelectedLine().set_serial(old_sr);
                                                return false;
                                            }
                                            else {
                                                (selectedOrder.get('orderLines')).each(_.bind( function(item) {
                                                    if (item.get_product().get('id') == sel_id && item.get('prodlot_id') == old_sr) {
                                                        alert('Same product is already assigned with same serial number !');
                                                        sr_no = null;
                                                        selectedOrder.getSelectedLine().set_serial(old_sr);
                                                        return false;
                                                    }
                                                }, this));
                                            }
                                        });
                                        $(this).dialog('destroy');
                                    } else {
                                        alert('Please enter valid serial number !');
                                    }
                                }},
                                {text: _t("Cancel"), click: function() { $(this).dialog('destroy'); }}
                            ]
                        }).open();
                        this.dialog.$el.html(QWeb.render("pos-assign_serial", self));
                        this.dialog.$el.find("input#pos_serial").focus();
                    }
                });

                $("#clear_serial").click(function() {
                    var self = this;
                    var selectedOrder = pos.get('selectedOrder');
                    if (selectedOrder && selectedOrder.getSelectedLine()) {
                        selectedOrder.getSelectedLine().set_serial(null);
                    } else {
                        alert("No record selected !");
                    }
                });
            }
        },
        close: function(){
            this._super();
            this.pos_widget.order_widget.set_numpad_state(null);
            this.pos_widget.payment_screen.set_numpad_state(null);
        }
    });

    module.Orderline = module.Orderline.extend({
        initialize: function(attr,options){
            this.pos = options.pos;
            this.order = options.order;
            this.product = options.product;
            this.price = options.product.get('price');
            this.quantity = 1;
            this.quantityStr = '1';
            this.discount = 0;
            this.discountStr = '0';
            this.type = 'unit';
            this.selected = false;
            this.prodlot_id = null;
        },
        set_serial: function(sr_no) {
            this.set('prodlot_id', sr_no)
        },
        get_serial: function() {
            return this.get('prodlot_id');
        },
        export_as_JSON: function() {
            return {
                prodlot_id: this.get_serial(),
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                discount: this.get_discount(),
                product_id: this.get_product().get('id')
            };
        },
        can_be_merged_with: function(orderline){
            if( this.get_product().get('id') !== orderline.get_product().get('id')){    //only orderline of the same product can be merged
                return false;
            }else if(this.get_product_type() !== orderline.get_product_type()){
                return false;
            }else if(this.get_discount() > 0){             // we don't merge discounted orderlines
                return false;
            }else if(this.price !== orderline.price){
                return false;
            } else if(this.get_serial()) {
                return false;
            }else{
                return true;
            }
        }
    });

    module.Order = module.Order.extend({
        initialize: function(attributes){
            Backbone.Model.prototype.initialize.apply(this, arguments);
            this.set({
                creationDate:   new Date(),
                orderLines:     new module.OrderlineCollection(),
                paymentLines:   new module.PaymentlineCollection(),
                name:           "Order " + this.generateUniqueId(),
                client:         null,
                client_id:      null,
                pricelist_val:  null,
                fiscal_val:     null
            });
            this.pos =     attributes.pos;
            this.selected_orderline = undefined;
            this.screen_data = {};  // see ScreenSelector
            this.receipt_type = 'receipt';  // 'receipt' || 'invoice'
            return this;
        },
        set_client_id: function(client_id) {
            this.set('client_id', client_id)
        },
        get_client_id: function(){
            return this.get('client_id');
        },
        get_client_name: function(){
            var client = this.get('client');
            return client ? client : "";
        },
        set_pricelist_val: function(client_id) {
            var self = this;
            if (client_id) {
                new instance.web.Model("res.partner").get_func("read")(parseInt(client_id), ['property_product_pricelist']).pipe(
                    function(result) {
                        self.set('pricelist_val', result.property_product_pricelist[0] || '');
                    }
                );
            }
        },
        get_pricelist: function() {
            return this.get('pricelist_val');
        },
        set_fiscal_val: function(client_id) {
            var self = this;
            if (client_id) {
                new instance.web.Model("res.partner").get_func("read")(parseInt(client_id), ['property_account_position']).pipe(
                    function(result) {
                        if (result && result.property_account_position) {
                            self.set('fiscal_val', result.property_account_position[0] || '');
                        }
                    }
                );
            }
        },
        get_fiscal_val: function() {
            return this.get('fiscal_val');
        },
        addProduct: function(product, options){
            var self = this;
            options = options || {};
            var attr = product.toJSON();
            attr.pos = this.pos;
            attr.order = this;
            var line = new module.Orderline({}, {pos: this.pos, order: this, product: product});
            var partner_id = parseInt(self.get_client_id());
            var pricelist_id = parseInt(self.get_pricelist());
            var fiscal_id = parseInt(this.get_fiscal_val());
            var uom = null;
            if (attr.id) {
                new instance.web.Model("product.product").get_func("read")(attr.id, ['serial_required']).pipe(
                    function(result) {
                        if (result && result.serial_required) {
                            self.dialog = new instance.web.Dialog(self, {
                                title: _t("Enter Serial Number"),
                                width: 320,
                                height: 180,
                                buttons: [
                                    {text: _t("Validate"), click: function() {
                                        var sr_no = self.dialog.$el.find("input#pos_serial").val();
                                        line.set_serial(sr_no);
                                        sr_no = jQuery.trim(sr_no);
                                        if (sr_no.length > 0) {
                                            new instance.web.Model("stock.production.lot").get_func("search_read")
                                                        ([['product_id', '=', attr.id], ['name', '=', sr_no]]).pipe(
                                                function(result) {
                                                    if (result && result.length > 0) {
                                                        alert('Same product is already assigned with same serial number !');
                                                        sr_no = null;
                                                        return false;
                                                    } else {
                                                        (self.get('orderLines')).each(_.bind( function(item) {
                                                            if (item.get_product().get('id') == attr.id && item.get('serial_no') == sr_no) {
                                                                alert('Same product is already assigned with same serial number !');
                                                                sr_no = null;
                                                                return false;
                                                            }
                                                        }, this));
                                                    }
                                                    if (sr_no != null) {
                                                        if(options.quantity !== undefined){
                                                            line.set_quantity(options.quantity);
                                                        }
                                                        if(options.price !== undefined){
                                                            line.set_unit_price(options.price);
                                                        }
                                                        var last_orderline = self.getLastOrderline();
                                                        if(last_orderline && last_orderline.serial_no == null
                                                                && last_orderline.can_be_merged_with(line) && options.merge !== false){
                                                            last_orderline.merge(line);
                                                            var qty = last_orderline.get_quantity();
                                                            if (partner_id && pricelist_id) {
                                                                new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], product.id, qty).pipe(
                                                                    function(res){
                                                                        if (res && res[pricelist_id]) {
                                                                            pricelist_value = parseFloat(res[pricelist_id].toFixed(2));
                                                                            if (pricelist_value) {
                                                                                last_orderline.set_unit_price(pricelist_value);
                                                                            }
                                                                        }
                                                                    }
                                                                );
                                                            }
                                                        } else {
                                                            self.get('orderLines').add(line);
                                                        }
                                                        self.selectLine(self.getLastOrderline());
                                                    }
                                                }
                                            );
                                            $(this).dialog("destroy");
                                       } else {
                                           alert('Please enter valid serial number !');
                                           return;
                                       }
                                    }},
                                    {text: _t("Cancel"), click: function() { $(this).dialog('destroy'); }}
                                ]
                            }).open();
                            self.dialog.$el.html(QWeb.render("pos-assign_serial", self));
                            self.dialog.$el.find("input#pos_serial").focus();
                        } else {
                            if(options.quantity !== undefined){
                                line.set_quantity(options.quantity);
                            }
                            if(options.price !== undefined){
                                line.set_unit_price(options.price);
                            }
                            var last_orderline = self.getLastOrderline();
                            if( last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false){
                                last_orderline.merge(line);
                                var qty = last_orderline.get_quantity();
                                if (partner_id && pricelist_id) {
                                    new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], product.id, qty).pipe(
                                        function(res){
                                            if (res && res[pricelist_id]) {
                                                pricelist_value = parseFloat(res[pricelist_id].toFixed(2));
                                                if (pricelist_value) {
                                                    last_orderline.set_unit_price(pricelist_value);
                                                }
                                            }
                                        }
                                    );
                                }
                            } else {
                                var pricelist_value = null;
                                if (partner_id && pricelist_id) {
//                                    var self = this;
                                    new instance.web.Model("product.template").get_func("read")(parseInt(product.id), ['uom_id']).pipe(
                                        function(result) {
                                            if (result && result.uom_id) {
                                                uom = result.uom_id[0];
                                            }
                                        }
                                    );
                                    new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], product.id, 1).pipe(
                                        function(res){
                                            pricelist_value = parseFloat(res[pricelist_id].toFixed(2));
                                            if (pricelist_value) {
                                                line.set_unit_price(pricelist_value);
                                                self.get('orderLines').add(line);
                                                self.selectLine(self.getLastOrderline());
                                            }
                                            else {
                                                self.get('orderLines').add(line);
                                                self.selectLine(self.getLastOrderline());
                                            }
                                        }
                                    );
                                } if (fiscal_id) {
                                    new instance.web.Model("account.fiscal.position").get_func('map_tax')(fiscal_id, product.get('taxes_id')).pipe(
                                        function(res){
                                            if (res) {
                                                product.set('taxes_id', res);
                                                self.get('orderLines').add(line);
                                            }
                                        }
                                    );
                                } else {
                                    self.get('orderLines').add(line);
                                }
                            }
                            self.selectLine(self.getLastOrderline());
                        }
                    }
                );
            }
        },
        exportAsJSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            (this.get('orderLines')).each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            (this.get('paymentLines')).each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));

            return {
                name: this.getName(),
                amount_paid: this.getPaidTotal(),
                amount_total: this.getTotalTaxIncluded(),
                amount_tax: this.getTax(),
                amount_return: this.getChange(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos.get('pos_session').id,
                partner_id: parseInt(this.get_client_id()) || "",
                user_id: this.pos.get('cashier') ? this.pos.get('cashier').id : this.pos.get('user').id
            };
        }
    });

    module.OrderWidget = module.OrderWidget.extend({
        set_value: function(val) {
            var order = this.pos.get('selectedOrder');
            if (order.get('orderLines').length !== 0) {
                var mode = this.numpadState.get('mode');
                if( mode === 'quantity'){
                    var partner_id = parseInt(order.get_client_id());
                    var pricelist_id = parseInt(order.get_pricelist());
                    if ((val != 'remove') && pricelist_id && order && order.getSelectedLine().get_product().id) {
                        var p_id = order.getSelectedLine().get_product().id;
                        if (! val) {
                            val = 1;
                        }
                        new instance.web.Model("product.pricelist").get_func('price_get')([pricelist_id], p_id, val).pipe(
                            function(res){
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
                }else if( mode === 'discount'){
                    order.getSelectedLine().set_discount(val);
                }else if( mode === 'price'){
                    order.getSelectedLine().set_unit_price(val);
                }
            } else {
                if (this.pos.get('selectedOrder')) {
                    this.pos.get('selectedOrder').destroy();
                    alert('Selected order has been cleared !');
                }
            }
        }
    });

    module.PaymentScreenWidget = module.PaymentScreenWidget.extend({
        show: function(){
            this._super();
            var self = this;

            if(this.pos.iface_cashdrawer){
                this.pos.proxy.open_cashbox();
            }

            this.set_numpad_state(this.pos_widget.numpad.state);

            this.invoice_button = this.add_action_button({
                    label: 'Facturar',
                    name: 'invoice',
                    icon: '/marcos_pos_ncf/static/src/img/invoice.png',
                    click: function(){
                        self.validateCurrentOrder({invoice: true});
                    }
                });

            this.updatePaymentSummary();
            this.line_refocus();
            $(".pos-actionbar-button-list").children().eq(2).remove()// remove de pos default validate button
        },
        close: function(){
            this._super();
            this.pos_widget.order_widget.set_numpad_state(null);
            this.pos_widget.payment_screen.set_numpad_state(null);
        },
        back: function() {
            this.pos_widget.screen_selector.set_current_screen(self.back_screen);
        },
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


            if(options.invoice){
                if (client_id == null) {
                    alert('Debe seleccionar un cliente!');
                    return;
                }
                // deactivate the validation button while we try to send the order
                this.pos_widget.action_bar.set_button_disabled('validation',true);
                this.pos_widget.action_bar.set_button_disabled('invoice',true);
                var order = currentOrder.exportAsJSON();
                this.db.add_order(order);
                last_order = this.db.get_orders();

                var rpc = (new instance.web.Model('pos.order')).call('create_from_ui',[[last_order[0]]],undefined,{shadow: true});
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
                                var fiscal_type = result[3] || 'final';
                                var client = result[4];
                                var branch = result[5]
                                var uid = result[6]
                                print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, ncf, rnc, fiscal_type, client, branch, uid, oid);
                            }else{
                                var invoice_id = result[0];
                                // this method call pdf to print
                                self.pos_widget.do_action('account.account_invoices',{additional_context:{
                                active_ids:[invoice_id]                                                }});

                            };
                        });
                    }
                    self.pos_widget.action_bar.set_button_disabled('validation',false);
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    self.pos.get('selectedOrder').destroy();
                });
            } else {
                this.pos.push_order(currentOrder.exportAsJSON())
                if(this.pos.iface_print_via_proxy){
                    this.pos.proxy.print_receipt(currentOrder.export_for_printing(), printer_host, printer_model, null, null, null);
                    this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                }else{
                    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                }
            }
        },
        updatePaymentSummary: function() {
            var currentOrder = this.pos.get('selectedOrder');
            var paidTotal = currentOrder.getPaidTotal();
            var dueTotal = currentOrder.getTotalTaxIncluded();
            var remaining = dueTotal > paidTotal ? dueTotal - paidTotal : 0;
            var change = paidTotal > dueTotal ? paidTotal - dueTotal : 0;

            this.$('#payment-due-total').html(this.format_currency(dueTotal));
            this.$('#payment-paid-total').html(this.format_currency(paidTotal));
            this.$('#payment-remaining').html(this.format_currency(remaining));
            this.$('#payment-change').html(this.format_currency(change));
            if(currentOrder.selected_orderline === undefined){
                remaining = 1;  // What is this ?
            }
            if(this.pos_widget.action_bar){
                this.pos_widget.action_bar.set_button_disabled('validation', remaining > 0);
                this.pos_widget.action_bar.set_button_disabled('invoice', remaining > 0);
            }
        }
    });

    instance.marcos_pos_ncf.PrintIpfVoucher = instance.web.form.FormWidget.extend({
        template: "print_ncf",
        start: function() {
            var self = this;
            var order_name = this.field_manager.get_field_value("name");
            var order_instance = new instance.web.Model("pos.order");
            this.$el.click(function() {
                order_instance.call("print_on_ipf", [order_name], {context: new instance.web.CompoundContext()}).then(function(result) {
                    console.log(result);
                });
            });
        }
    });

    instance.web.form.custom_widgets.add("printipf", "instance.marcos_pos_ncf.PrintIpfVoucher");
};