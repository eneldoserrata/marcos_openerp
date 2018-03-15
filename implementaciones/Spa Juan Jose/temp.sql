[smalto][reporte para comiciones]
select p.name, o.date_order, ol.name, e.name_related, s.name, ap.state, ol.price_subtotal, ol.price_unit, ol.price_subtotal_incl from salon_spa_appointment as ap
  join pos_order_line as ol on ap.order_line_id = ol.id
  join pos_order as o on ol.order_id = o.id
  join res_partner as p on o.partner_id = p.id
  join hr_employee as e on ap.employee_id = e.id
  join salon_spa_space as s on ap.space_id = s.id
  where o.date_order between '2014-06-21 00:00:00.00' and '2014-07-20 24:00:00.00'
  order by o.date_order

[coworokingtemp][Movimientos de stock]
SELECT
  product_template.name,
  sum(stock_move.product_qty/product_uom.factor),
  product_template.list_price,
  product_template.standard_price,
  stock_location.name
FROM
  public.stock_move,
  public.product_template,
  public.product_uom,
  public.stock_location
WHERE
  stock_move.product_id = product_template.id AND
  stock_move.product_uos = product_uom.id AND
  stock_move.location_dest_id = stock_location.id AND
  stock_move.state = 'done' AND
  (stock_location.name = 'Stock' OR stock_location.name = 'Customers')
group by
   product_template.name,
   product_template.list_price,
   product_template.standard_price,
   stock_location.name
order by
  product_template.name

[update purchase_order to done]

update purchase_order set state = 'done' where id in
(select p.id from purchase_order as p join account_invoice as i on i.origin = p.name and i.state = 'paid')

