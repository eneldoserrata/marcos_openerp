openerp.marcos_pos_prod_avail = function (instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    
    instance.point_of_sale.ProductCategoriesWidget = instance.point_of_sale.ProductCategoriesWidget.extend({
        fetch: function(model, fields, domain, ctx){
            return new instance.web.Model(model).query(fields).filter(domain).context(ctx).all()
        },
        search_and_categories: function(category){
            var self = this;
            var order = this.pos.get('selectedOrder');
            var ret_o_id = order.get_ret_o_id();
            if (!ret_o_id || ret_o_id == 'Missing Receipt') {
                var shop = this.pos.get('shop');
                var pids = [];
                // find all products belonging to the current category
                var products = this.pos.db.get_product_by_category(this.category.id);
                
                _.each(products, _.bind( function (pid) {
                    pids.push(parseInt(pid.id));
                }));

                var products1 = self.fetch(
                    'product.product', 
                    ['name', 'list_price','price','pos_categ_id', 'taxes_id', 'ean13', 'qty_available',
                     'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description'],
                    [['id','in',pids]],
                    {pricelist: shop.pricelist_id[0], 'qty_exists': self.pos.get("pos_config").not_show_zero_stock} // context for price
                ).then(function(products1){
                    self.pos.get('products').reset(products1);
                });
                //self.pos.get('products').reset(products);
    
                // filter the products according to the search string
//                this.$('.searchbox input').keyup(function(){
//                    query = $(this).val().toLowerCase();
//                    if(query){
//                        var products = self.pos.db.search_product_in_category(self.category.id, query);
//                        self.pos.get('products').reset(products);
//                        self.$('.search-clear').fadeIn();
//                    }else{
//                        var products = self.pos.db.get_product_by_category(self.category.id);
//                        self.pos.get('products').reset(products);
//                        self.$('.search-clear').fadeOut();
//                    }
//                });
                this.$('.searchbox input').keyup(function(event){
                    query = $(this).val().toLowerCase();
                    if (event.keyCode === 13 && self.pos.get('pos_config').live_search === false) {
                        if(query){
                            var products = self.pos.db.search_product_in_category(self.category.id, query);
                            self.pos.get('products').reset(products);
                            self.$('.search-clear').fadeIn();
                        }else{
                            var products = self.pos.db.get_product_by_category(self.category.id);
                            self.pos.get('products').reset(products);
                            self.$('.search-clear').fadeOut();
                        }
                    } else if (self.pos.get('pos_config').live_search === true){
                        if(query){
                            var products = self.pos.db.search_product_in_category(self.category.id, query);
                            self.pos.get('products').reset(products);
                            self.$('.search-clear').fadeIn();
                        }else{
                            var products = self.pos.db.get_product_by_category(self.category.id);
                            self.pos.get('products').reset(products);
                            self.$('.search-clear').fadeOut();
                        }
                    }
                });
    
                this.$('.searchbox input').click(function(){}); //Why ???
    
                //reset the search when clicking on reset
                this.$('.search-clear').click(function(){
                    var products = self.pos.db.get_product_by_category(self.category.id);
                    self.pos.get('products').reset(products);
                    self.$('.searchbox input').val('').focus();
                    self.$('.search-clear').fadeOut();
                });
            }
        }
    });

    instance.point_of_sale.PosModel = instance.point_of_sale.PosModel.extend({
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

                    return self.fetch('res.currency',['symbol','position','rounding','accuracy'],[['id','=',self.get('company').currency_id[0]]]);
                }).then(function(currencies){
                    self.set('currency',currencies[0]);

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
                         'not_show_zero_stock', 'live_search', 'bill_credit'], // by eneldo select two nwe field
                        [['id','=', self.get('pos_session').config_id[0]]]
                    );
                }).then(function(configs){
                    var pos_config = configs[0];
                    self.set('pos_config', pos_config);
                    self.iface_electronic_scale    =  !!pos_config.iface_electronic_scale;  
                    self.iface_print_via_proxy     =  !!pos_config.iface_print_via_proxy;
                    self.iface_vkeyboard           =  !!pos_config.iface_vkeyboard; 
                    self.iface_self_checkout       =  !!pos_config.iface_self_checkout;
                    self.iface_cashdrawer          =  !!pos_config.iface_cashdrawer;

                    return self.fetch('sale.shop',[],[['id','=',pos_config.shop_id[0]]]);
                }).then(function(shops){
                    self.set('shop',shops[0]);

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
                    )

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
                    self.set({'cashRegisters' : new instance.point_of_sale.CashRegisterCollection(self.get('bank_statements'))});
                });
            return loaded;
        }
    });
}