update product_template set uom_id = 1 where uom_id !=1;
update account_invoice_line set uos_id = 1 where invoice_id in (select id from account_invoice where journal_id = 11);
update account_move_line set product_uom_id = 1 where name like '%POSL%';
update stock_move set product_uom = 1, product_uos = 1 where product_uos != 1 and origin like '%POS%';
