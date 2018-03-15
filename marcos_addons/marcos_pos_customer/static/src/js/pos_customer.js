openerp.marcos_pos_customer = function (instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    
    var round_pr = instance.web.round_precision;

    instance.point_of_sale.ProductScreenWidget = instance.point_of_sale.ProductScreenWidget.extend({
        init: function() {
            this._super.apply(this, arguments);
        },
        start:function(){
            
            var self = this;
            this.product_categories_widget = new instance.point_of_sale.ProductCategoriesWidget(this,{});
            this.product_categories_widget.replace($('.placeholder-ProductCategoriesWidget'));
            
            this.product_list_widget = new instance.point_of_sale.ProductListWidget(this,{
                click_product_action: function(product){
                    if(product.get('to_weight') && self.pos.iface_electronic_scale){
                        self.pos_widget.screen_selector.set_current_screen(self.scale_screen, {product: product});
                    }else{
                        self.pos.get('selectedOrder').addProduct(product);
                    }
                }
            });
            this.product_list_widget.replace($('.placeholder-ProductListWidget'));
            
            orderView = new instance.point_of_sale.OrderWidget(this, {});
            pos = this.pos;
            selectedOrder = pos.get('selectedOrder');
            if ($('button.select-order').length == 1) {
//                pos = this.pos;
                $("#customer_link").click(function() {
                    selectedOrder = pos.get('selectedOrder');
                    var self = this;
                            var pop = new instance.web.form.SelectCreatePopup(this);
                            pop.select_element(
                                'res.partner',
                                {
                                    title: 'Seleccione cliente',
                                    initial_view: 'search',
                                    disable_multiple_selection: true
                                },
                                [['customer', '=', true]],
                                {'search_default_customer': true}
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
                
                $("#create_so").click(function(options) {
                    selectedOrder = pos.get('selectedOrder');
                    currentOrderLines = selectedOrder.get('orderLines');
                    orderLines = [];
                    (currentOrderLines).each(_.bind( function(item) {
                        return orderLines.push(item.export_as_JSON());
                    }, this));

                    customer_id = selectedOrder.get_client_id() || '';

                    if (orderLines.length === 0) {
                        ////////////open dialog to seacrh quotation
                        pos.add_new_order();
                        selectedOrder = pos.get('selectedOrder');
                        pop = new instance.web.form.SelectCreatePopup(this);
                        pop.select_element(
                            "sale.order",
                            {
                                title: "Buscar cotizacion",
                                initial_view: "search",
                                disable_multiple_selection: true
                            },
                            [['state', '=', 'draft']],
                            {'search_default_customer': true}
                        );
                        pop.on("elements_selected", self, function(element_ids) {
                            var dataset = new instance.web.DataSetStatic(self, 'sale.order', {});
                            dataset.name_get(element_ids).done(function(data) {
                                pos_order_obj = new instance.web.Model("sale.order");
                                pos_order_obj.get_func("search_read")
                                ([['id', '=', data[0][0]]],['id', 'pos_reference', 'partner_id']).pipe(
                                    function(result){
                                        if (result && result.length == 1) {
                                            selectedOrder.set_client_id(result[0].partner_id[0]);
                                            selectedOrder.set_client(result[0].partner_id[1]);

                                            new instance.web.Model("sale.order.line").get_func("search_read")
                                                ([['order_id', '=', result[0].id]], []).pipe(
                                                    function(result){
                                                        if (result) {
                                                            var products = [];
                                                            _.each(result, function(res) {
                                                                var product = pos.db.get_product_by_id(res.product_id[0]);
                                                                products.push(product);
                                                            });
                                                            pos.get('products').reset(products);
                                                            products = null;
                                                            product = null
                                                            _.each(result, function(res){
                                                                var product = pos.get("products").where({id: res.product_id[0]})[0];
                                                                var options = {
                                                                    quantity: res.product_uom_qty,
                                                                    price: res.price_unit
                                                                }
                                                                selectedOrder.addProduct(product, options);
                                                            });
                                                        };
                                                    });
                                        };
                                    });
                            });
                        });
                    } else if (!customer_id) {
                        $("#customer_link").click();
                        return
                    } else {
                        new instance.web.Model('sale.order').call('create_sales_order', [orderLines, customer_id], {context: {"shop_id": pos.shop_id}})
                        .then(function(res){
                            if (res) {
                                this.dialog = new instance.web.Dialog(this, {
                                                        title: "Cotizacion",
                                                        width: 320,
                                                        height: 150,
                                                        buttons: [
                                                            {"text": "Por email",
                                                            click: function(){
                                                                new instance.web.Model('sale.order').call('action_quotation_send', [[res.sale_id]], {context: new instance.web.CompoundContext()}).then(function(result){
                                                                    self.do_action(result);
                                                                });
                                                                selectedOrder.destroy();
                                                                $(this).dialog('destroy');
                                                            }},
                                                            {"text": "Por la impresora",
                                                            click: function(){
                                                                new instance.web.Model('sale.order').call('get_quotation_report', [[res.sale_id]], {context: new instance.web.CompoundContext()}).then(function(result){
                                                                    self.do_action(result);
                                                                });
                                                                selectedOrder.destroy();
                                                                $(this).dialog('destroy');
                                                            }}
                                                        ]
                                                    }).open();
                                this.dialog.$el.html("Se genero la cotizacion No:"+ res.sale_no +" Como desea enviarla?");
                            }
                            else {
                                return alert('Ocurrio un error miestras se creaba la cotización !');
                            }
                        });
                    }
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
                            title: _t("Numero Serial"),
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
                                                alert('Otro producto ya se ha asignado con el mismo número de serie!');
                                                sr_no = null;
                                                selectedOrder.getSelectedLine().set_serial(old_sr);
                                                return false;
                                            }
                                            else {
                                                (selectedOrder.get('orderLines')).each(_.bind( function(item) {
                                                    if (item.get_product().get('id') == sel_id && item.get('prodlot_id') == old_sr) {
                                                        alert('Otro producto ya se ha asignado con el mismo número de serie!');
                                                        sr_no = null;
                                                        selectedOrder.getSelectedLine().set_serial(old_sr);
                                                        return false;
                                                    }
                                                }, this));
                                            }
                                        });
                                        $(this).dialog('destroy');
                                    } else {
                                        alert('Por favor, introduzca el número de serie válido!');
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
                        alert("Debe seleccionar un producto!");
                    }
                });
            }
            $('#return_order_ref').html('');
            pos = this.pos;
            hide_controls = this.hide_controls;
            var fiscal_type = null;

            $("span#return_order").click(function() {
                var self = this;
                pos.add_new_order();
                $("span#return_order").css('background', 'blue');
                $("span#sale_mode").css('background', '');
                var selectedOrder = pos.get('selectedOrder');
                this.dialog = new instance.web.Dialog(this, {
                    title: _t("Devolución"),
                    width: 320,
                    height: 180,
                    beforeClose: function(){
                        pos.get('selectedOrder').destroy()
                        $("span#sale_mode").click();
                        pos.set({ selectedOrder: pos.get('orders').last() });
                    },
                    buttons: [
                        {text: _t("Validate"), click: function() {
                            var ret_o_ref = self.dialog.$el.find("input#return_order_number").val().trim().toUpperCase();

                            if (ret_o_ref.length > 0) {
                                pos_order_obj = new instance.web.Model("pos.order");
                                pos_order_obj.get_func("search_read")
                                            ([['name', '=', ret_o_ref],['parent_return_order', '=', '']],
                                            ['id', 'name', 'partner_id', 'pos_reference']).pipe(
                                    function(result) {
                                        if (result && result.length == 1) {
                                            selectedOrder.set_client_id(result[0].partner_id[0]);
                                            selectedOrder.set_client(result[0].partner_id[1]);

                                            pos_order_obj.call("get_property_account_position_fiscal_type", [selectedOrder.get_client_id(), result[0].id],
                                                {context: new instance.web.CompoundContext()}).then(
                                                function(result){
                                                    if (result) {
                                                        products = [];
                                                        _.each(result[1],function(res) {
                                                            product = pos.db.get_product_by_id(res.product_id[0]);
                                                            product.price = res.price_unit;
                                                            if (result[0]){
                                                                product.taxes_id[0] = result[0];
                                                            };
                                                            products.push(product);
                                                        });
                                                        pos.get('products').reset(products);
                                                    };
                                                });

                                            selectedOrder.get_oid(result[0].id);
                                            selectedOrder.set_ret_o_ref(result[0].pos_reference);
                                            hide_controls();
                                            pos_order_obj.call('get_partner_temp_name',  [result[0].id], {context: new instance.web.CompoundContext()}).then(function(result) {
                                                $("#order-selector").append("<button id='refound_label'>"+ "Devolución de la " + result.order + " de " + result.temp_name +"</button>")
                                            });
                                            $('#return_order_ref').html(result[0].pos_reference);
                                        } else {
                                            $("span#sale_mode").click();
                                            var error_str = _t('Por favor, introduzca el número de referencia correcto!');
                                            var error_dialog = new instance.web.Dialog(this, { 
                                                width: '310',
                                                beforeClose: function(){
                                                    pos.get('selectedOrder').destroy()
                                                    $("span#sale_mode").click();
                                                    pos.set({ selectedOrder: pos.get('orders').last() });
                                                },
                                                buttons: [{text: _t("Close"), click: function() {
                                                    $(this).dialog('close');
                                                    $(this).dialog('destroy');
                                                }}]
                                            }).open();
                                            error_dialog.$el.append(
                                                '<span id="error_str" style="font-size:16px;">' + error_str + '</span>');
                                        }
                                    }
                                );
                                $(this).dialog('destroy');
                            } else {
                                $("span#sale_mode").click();
                                var error_str =_t('Por favor, introduzca el número de referencia correcto!');
                                var error_dialog = new instance.web.Dialog(this, { 
                                    width: '310',
                                    beforeClose: function(){
                                        pos.get('selectedOrder').destroy()
                                        $("span#sale_mode").click();
                                        pos.set({ selectedOrder: pos.get('orders').last() });
                                    },
                                    buttons: [{text: _t("Close"), click: function() {
                                        $(this).dialog('close');
                                        $(this).dialog('destroy');
                                    }}]
                                }).open();
                                error_dialog.$el.append(
                                    '<span id="error_str" style="font-size:18px;">' + error_str + '</span>');

                            }
                        }},
                        {text: _t("Cancel"), click: function() {
                            $(this).dialog('close');
                            $(this).dialog('destroy');
                        }}
                    ]
                }).open();
                this.dialog.$el.html(QWeb.render("pos-return-order", self));
                this.dialog.$el.find("input#return_order_number").focus();
            });
            
            $("span#sale_mode").click(function(event) {

                var selectedOrder = pos.get('selectedOrder');
                var id = $(event.target).data("category-id");
                selectedOrder.set_ret_o_id('');
                var category = pos.db.get_category_by_id(id);
                self.product_categories_widget.set_category(category);
                self.product_categories_widget.renderElement();
                
                $("span#sale_mode").css('background', 'blue');
                $("span#return_order").css('background', '');
                selectedOrder.set_ret_o_ref('');
                $('#return_order_ref').html('');
            });

        },
        close: function(){
            this._super();
            this.pos_widget.order_widget.set_numpad_state(null);
            this.pos_widget.payment_screen.set_numpad_state(null);
        },
        hide_controls: function(){
            $(".header-cell").hide();
            $(".selection-area").hide();
            $("#orders").hide();
            $(".neworder-button").hide();
            $(".number-char").hide();
            $('*[data-mode="quantity"]').hide();
            $('*[data-mode="discount"]').hide();
            $('*[data-mode="price"]').hide();
            $('#numpad-minus').hide();
        }
    });
    
    instance.point_of_sale.ReceiptScreenWidget = instance.point_of_sale.ReceiptScreenWidget.extend({
        finishOrder: function() {
            this.pos.get('selectedOrder').destroy();
            $("span#sale_mode").css('background', 'blue');
            $("span#return_order").css('background', '');
            $('#return_order_ref').html('');
            $('#return_order_number').val('');
        }
    });
    
    instance.point_of_sale.Orderline = instance.point_of_sale.Orderline.extend({
        init: function() {
            this._super.apply(this, arguments);
        },
        initialize: function(attr,options){
            this.pos = options.pos;
            this.order = this.pos.get('selectedOrder'); //options.order;
            this.product = options.product;
            this.price   = options.product.get('price');
            this.quantity = 1;
            this.quantityStr = '1';
            this.discount = 0;
            this.discountStr = '0';
            this.type = 'unit';
            this.selected = false;
            this.prodlot_id = null;
            this.oid = null;
        },
        set_quantity: function(quantity){
            if(quantity === 'remove'){
                this.order.removeOrderline(this);
                this.set_oid('');
                return;
            }else{
                var quant = Math.max(parseFloat(quantity) || 0, 0);
                var unit = this.get_unit();
                if(unit){
                    this.quantity    = Math.max(unit.rounding, round_pr(quant, unit.rounding));
                    this.quantityStr = this.quantity.toFixed(Math.max(0,Math.ceil(Math.log(1.0 / unit.rounding) / Math.log(10))));
                }else{
                    this.quantity    = quant;
                    this.quantityStr = '' + this.quantity;
                }
            }
            this.trigger('change');
        },
        set_serial: function(sr_no) {
            this.set('prodlot_id', sr_no)
        },
        get_serial: function() {
            return this.get('prodlot_id');
        },
        export_as_JSON: function() {
            var self = this;
            var oid = this.get_oid();
            var qty = this.get_quantity();
            var pos = this.pos;
            if (oid) {
                new instance.web.Model("pos.order.line").get_func("search_read")
                            ([['order_id', '=', oid],['product_id', '=', this.get_product().get('id')],['return_qty', '>', 0]], ['return_qty', 'id']).pipe(
                    function(result) {
                        if (result) {
                            if (parseFloat(result[0].return_qty) > 0 && parseFloat(qty) <= parseFloat(result[0].return_qty)) {
                                return_qty = parseFloat(result[0].return_qty) + parseFloat(qty);
                                new instance.web.Model("pos.order.line").get_func("write")
                                                (result[0].id, {'return_qty':return_qty});
                            }
                        }
                    }
                );
            } else {
                var return_qty = this.get_quantity();
            }
            var order_ref = $('#return_order_ref').html();
            if (order_ref) {
                qty = this.get_quantity() * -1;
            }
            return {
                prodlot_id: this.get_serial(),
                qty: qty,
                return_qty: parseFloat(return_qty),
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
        },
        set_oid: function(oid) {
            this.set('oid', oid)
        },
        get_oid: function() {
            return this.get('oid');
        }
    });
    
    instance.point_of_sale.Order = instance.point_of_sale.Order.extend({
        initialize: function(attributes){
            Backbone.Model.prototype.initialize.apply(this, arguments);
            this.set({
                creationDate:   new Date(),
                orderLines:     new instance.point_of_sale.OrderlineCollection(),
                paymentLines:   new instance.point_of_sale.PaymentlineCollection(),
                name:           "Order " + this.generateUniqueId(),
                client:         null,
                client_id:      null,
                pricelist_val:  null,
                fiscal_val:     null,
                ret_o_id:       null,
                ret_o_ref:      null
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
                            new instance.web.Model("account.fiscal.position").get_func("read")(self.get("fiscal_val"), ['fiscal_type']).pipe(
                                function(result){
                                    self.set('fiscal_type', result.fiscal_type || '');
                            });
                        };
                    }
                );
            }
        },
        get_fiscal_val: function() {
            return this.get('fiscal_val');
        },
        set_ret_o_id: function(ret_o_id) {
            this.set('ret_o_id', ret_o_id)
        },
        get_ret_o_id: function(){
            return this.get('ret_o_id');
        },
        set_ret_o_ref: function(ret_o_ref) {
            this.set('ret_o_ref', ret_o_ref)
        },
        get_ret_o_ref: function(){
            return this.get('ret_o_ref');
        },
        getName: function() {
            var ret_o_ref = this.get_ret_o_ref();
            if (ret_o_ref && ret_o_ref.toString() != 'Missing Receipt') {
                return this.get_ret_o_ref();
            }
            return this.get('name');
        },
        addProduct: function(product, options){
            var self = this;
            options = options || {};
            var attr = product.toJSON();
            attr.pos = this.pos;
            attr.order = this;
            
            var ret_o_id = this.get_ret_o_id();
            if (ret_o_id && ret_o_id.toString() != 'Missing Receipt') {
                var pids = [];
                new instance.web.Model("pos.order.line").get_func("search_read")
                                    ([['order_id', '=', ret_o_id],['product_id', '=', attr.id],['return_qty', '>', 0]], 
                                    ['return_qty', 'id', 'price_unit', 'discount']).pipe(
                    function(result) {
                        if (result && result.length > 0) {
                            if (result[0].return_qty > 0) {
                                add_prod = true;
                                (self.get('orderLines')).each(_.bind( function(item) {
                                    if (attr.id == item.get_product().get('id') && 
                                        result[0].return_qty <= item.quantity) {
                                        var error_str = _t('No se puede volver más productos!');
                                        var error_dialog = new instance.web.Dialog(this, { 
                                            width: '300',
                                            buttons: [{text: _t("Close"), click: function() { $(this).dialog('destroy'); }}]
                                        }).open();
                                        error_dialog.$el.append(
                                            '<span id="error_str" style="font-size:18px;">' + error_str + '</span>');
                                        add_prod = false;
                                    }
                                }, self));
                                
                                if (add_prod) {
                                    var line = new instance.point_of_sale.Orderline({}, {pos: attr.pos, order: self, product: product});
                                    var partner_id = parseInt(self.get_client_id());
                                    var pricelist_id = parseInt(self.get_pricelist());
                                    var fiscal_id = parseInt(self.get_fiscal_val());
                                    var uom = null;
                                    if (attr.id) {
                                        new instance.web.Model("product.product").get_func("read")(attr.id, ['serial_required']).pipe(
                                            function(result) {
                                                if (result && result.serial_required) {
                                                    self.dialog = new instance.web.Dialog(self, {
                                                        title: _t("Introduzca el número de serie"),
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
                                                                                alert('Otro producto ya se ha asignado con el mismo número de serie!');
                                                                                sr_no = null;
                                                                                return false;
                                                                            } else {
                                                                                (self.get('orderLines')).each(_.bind( function(item) {
                                                                                    if (item.get_product().get('id') == attr.id && item.get('serial_no') == sr_no) {
                                                                                        alert('Otro producto ya se ha asignado con el mismo número de serie!');
                                                                                        sr_no = null;
                                                                                        return false;
                                                                                    }
                                                                                }, this));
                                                                            }
                                                                            if (sr_no != null) {
                                                                                line.set_oid(ret_o_id);
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
                                                                   alert('Por favor, introduzca el número de serie válido!');
                                                                   return;
                                                               }
                                                            }},
                                                            {text: _t("Cancel"), click: function() { $(this).dialog('destroy'); }}
                                                        ]
                                                    }).open();
                                                    self.dialog.$el.html(QWeb.render("pos-assign_serial", self));
                                                    self.dialog.$el.find("input#pos_serial").focus();
                                                } else {
                                                    line.set_oid(ret_o_id);
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
                                                            // var self = this;
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
                                }
                            } else {
                                var error_str = _t('Por favor, compruebe la cantidad del producto seleccionado y producto vendido!');
                                var error_dialog = new instance.web.Dialog(this, { 
                                    width: '350',
                                    buttons: [{text: _t("Close"), click: function() { $(this).dialog('destroy'); }}]
                                }).open();
                                error_dialog.$el.append(
                                    '<span id="error_str" style="font-size:18px;">' + error_str + '</span>');
                                return;
                            }
                    } else {
                        var error_str = _t('Product is not in order list !');
                        var error_dialog = new instance.web.Dialog(this, { 
                            width: '300',
                            buttons: [{text: _t("Close"), click: function() { $(this).dialog('destroy'); }}]
                        }).open();
                        error_dialog.$el.append(
                            '<span id="error_str" style="font-size:18px;">' + error_str + '</span>');
                    }
                });
            } else {
                var line = new instance.point_of_sale.Orderline({}, {pos: attr.pos, order: attr, product: product});
                var partner_id = parseInt(self.get_client_id());
                var pricelist_id = parseInt(self.get_pricelist());
                var fiscal_id = parseInt(self.get_fiscal_val());
                var uom = null;
                if (attr.id) {
                    new instance.web.Model("product.product").get_func("read")(attr.id, ['serial_required']).pipe(
                        function(result) {
                            if (result && result.serial_required) {
                                self.dialog = new instance.web.Dialog(self, {
                                    title: _t("Introduzca el número de serie"),
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
                                                            alert('Otro producto ya se ha asignado con el mismo número de serie!');
                                                            sr_no = null;
                                                            return false;
                                                        } else {
                                                            (self.get('orderLines')).each(_.bind( function(item) {
                                                                if (item.get_product().get('id') == attr.id && item.get('serial_no') == sr_no) {
                                                                    alert('Mismo producto ya se ha asignado con el mismo número de serie!');
                                                                    sr_no = null;
                                                                    return false;
                                                                }
                                                            }, this));
                                                        }
                                                        if (sr_no != null) {
                                                            if (ret_o_id && ret_o_id.toString() != 'Missing Receipt') {
                                                                line.set_oid(ret_o_id);
                                                            }
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
                                               alert('Por favor, introduzca el número de serie válido!');
                                               return;
                                           }
                                        }},
                                        {text: _t("Cancel"), click: function() { $(this).dialog('destroy'); }}
                                    ]
                                }).open();
                                self.dialog.$el.html(QWeb.render("pos-assign_serial", self));
                                self.dialog.$el.find("input#pos_serial").focus();
                            } else {
                                if (ret_o_id && ret_o_id.toString() != 'Missing Receipt') {
                                    line.set_oid(ret_o_id);
                                }
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
            }
        },
        exportAsJSON: function() {
            var orderLines, paymentLines;
            parent_return_order = '';
            
            var ret_o_id = this.get_ret_o_id();
            var ret_o_ref = this.get_ret_o_ref();
            var return_seq = 0;
            
            orderLines = [];
            (this.get('orderLines')).each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            (this.get('paymentLines')).each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            
            var barcode_val = this.getName();
            if (barcode_val.indexOf('Order') != -1) {
                var vals = barcode_val.split('Order ');
                if (vals) {
                    barcode = vals[1];
                    $("#barcode1").barcode(barcode, "ean13");
                }
            }
            
            if (ret_o_id) {
                parent_return_order = this.get_ret_o_id();
            }
            var note = $('#pos-remark').val();
            
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
                user_id: this.pos.get('cashier') ? this.pos.get('cashier').id : this.pos.get('user').id,
                parent_return_order: parent_return_order, // Required to create paid return order
                return_seq: return_seq || 0,
                note: note || ''
            };
        }
    });
    
    instance.point_of_sale.PaymentScreenWidget = instance.point_of_sale.PaymentScreenWidget.extend({
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
                    icon: '/marcos_pos_customer/static/src/img/invoice.png',
                    click: function(){
                        self.validateCurrentOrder({invoice: true});
                    }
                });

            this.updatePaymentSummary();
            this.line_refocus();
            //$(".pos-actionbar-button-list").children().eq(2).remove()// remove de pos default validate button
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
            
            var currentOrder = this.pos.get('selectedOrder');
            client_id = currentOrder.get_client_id();
            if(options.invoice){
                if (client_id == null) {
                    alert('No se a selecciona ningun Cliente para poder editarlo!');
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
                            invoice_id = result;
                            self.pos_widget.do_action('account.account_invoices',{additional_context:{ 
                                active_ids:[invoice_id]
                            }});
                        });
                    }
                    self.pos_widget.action_bar.set_button_disabled('validation',false);
                    self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    self.pos.get('selectedOrder').destroy();
                });
            } else {
                self.pos.push_order(currentOrder.exportAsJSON())
                if(self.pos.iface_print_via_proxy){
                    self.pos.proxy.print_receipt(currentOrder.export_for_printing());
                    self.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                }else{
                    this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                }
            }
        },
        updatePaymentSummary: function() {
            var currentOrder = this.pos.get('selectedOrder');
            var paidTotal = currentOrder.getPaidTotal();
            if (currentOrder.get("fiscal_type") === "special"){
                var dueTotal = currentOrder.getTotalTaxExcluded();
            } else {
                var dueTotal = currentOrder.getTotalTaxIncluded();
            };

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

}