# -*- coding: utf-8 -*-
__author__ = "Eneldo Serrata"
import psycopg2
from openerp.tools.image import image_resize_image_big, image_resize_image_medium, image_resize_image_small
import base64
import re

conn = psycopg2.connect(dbname='xxxx', user='xxxxx', password='xxxx', host="127.0.0.1")

cur = conn.cursor()
cur.execute("select * from productos")
rows = cur.fetchall()

id = 10000
count = 0
for row in rows:
    count += 1
    id += 1#row[1]

    if row[41]:
        try:
            i = open('fotos/{}'.format(row[41]), 'rb').read()
            base = base64.b64encode(i)
            img_big = image_resize_image_big(base)
            img_med = image_resize_image_medium(base)
            #img_small = image_resize_image_medium(base)
        except:
            img_big = None
            img_med = None
            #img_small = None
    else:
        img_big = None
        img_med = None
        #img_small = None

    ret = re.sub(r'(([(\[].*[\)\]].?)|((?<!\/)[A-Z]{,3}\d+\s*))$', '', row[9])

    produc = {
        "IDCOMPANIA": row[0],
        "IDPRODUCTO": row[1],
        "PRO_REFERENCIA": row[2],
        "IDUSUARIO": row[3],
        "IDMEDIDA": row[4],
        "IDCOLOR": row[5],
        "IDGRUPO": row[6],
        "IDSUBGRUPO": row[7],
        "PRO_BARRA": row[8],
        "PRO_NOMBRE": ret,
        "PRO_STATUS": row[10],
        "PRO_EXISTENCIA": row[11],
        "PRO_REORDEN": row[12],
        "PRO_PRECIO1": row[13],
        "PRO_PRECIO2": row[14]*1.18,
        "PRO_PRECIO3": row[15],
        "PRO_PRECIO4": row[16],
        "PRO_DESC1": row[17],
        "PRO_DESC2": row[18],
        "PRO_DESC3": row[19],
        "PRO_DESC4": row[20],
        "PRO_REVAJA": row[21],
        "PRO_COSTORD": row[22]*1.18,
        "PRO_COSTOUS": row[23],
        "PRO_DESCORTA": row[24],
        "PRO_ITBIS": row[25],
        "PRO_DESCUENTO": row[26],
        "PRO_CUENTA": row[27],
        "PRO_MODIFICAPRECIO": row[28],
        "PRO_UBICACION": row[29],
        "PRO_FISICO": row[30],
        "PRO_CTAINGRESO": row[31],
        "PRO_CTACOSTO": row[32],
        "PRO_TIPOEXISTENCIA": row[33],
        #"PRO_FOTO": img,
        "PRO_MODDESCRIPCION": row[35],
        "PRO_UTI1": row[36],
        "PRO_UTI2": row[37],
        "PRO_UTI3": row[38],
        "PRO_ATE1": row[39],
        "PRO_ATE2": row[40],
        "IMAGEN":  row[41] or None,
        "DESCRIPCION": None,#row[42],
        "WEB": row[43],
        "PRO_PRECIO5": row[44],
        "PRO_PRECIO6": row[45],
        "PRO_PRECIO7": row[46],
        "PRO_UTI4": row[47],
        "PRO_UTI5": row[48],
        "PRO_UTI6": row[49],
        "PRO_UTI7": row[50],
        "DESCRIPCION_CORTA": None, #row[51],
        "ESPECIAL": row[52]
    }

    # import pdb; pdb.set_trace()

    #{'PRO_REFERENCIA': '1555', 'PRO_DESCUENTO': None, 'IDUSUARIO': 'EAS', 'PRO_REVAJA': 'S', 'IDCOLOR': None, 'IMAGEN': None, 'PRO_PRECIO7': Decimal('0.00'), 'PRO_EXISTENCIA': Decimal('7.00'), 'PRO_STATUS': 'ACT', 'PRO_BARRA': None, 'PRO_DESC4': None, 'IDGRUPO': 4, 'PRO_CTAINGRESO': None, 'PRO_DESC2': None, 'PRO_DESC3': None, 'PRO_DESC1': None, 'WEB': <read-only buffer for 0x10c0a6350, size 22, offset 0 at 0x10c2a89f0>, 'PRO_FISICO': Decimal('0.00'), 'PRO_CTACOSTO': None, 'PRO_FOTO': <read-only buffer for 0x10c0a6290, size 470726, offset 0 at 0x10c29bdf0>, 'PRO_COSTOUS': Decimal('1.11'), 'PRO_UTI4': Decimal('0.00'), 'PRO_UTI5': Decimal('-100.00'), 'PRO_UTI6': Decimal('-100.00'), 'PRO_UTI7': Decimal('-100.00'), 'PRO_UTI1': 'N', 'PRO_UTI2': Decimal('30.01'), 'PRO_UTI3': Decimal('14.99'), 'PRO_MODIFICAPRECIO': 'True', 'PRO_DESCORTA': None, 'PRO_UBICACION': None, 'PRO_PRECIO1': Decimal('60.61'), 'PRO_PRECIO3': Decimal('55.94'), 'PRO_PRECIO2': Decimal('53.61'), 'PRO_PRECIO5': None, 'PRO_PRECIO4': Decimal('0.00'), 'PRO_CUENTA': '102-00', 'PRO_PRECIO6': Decimal('0.00'), 'IDMEDIDA': 5, 'IDPRODUCTO': 1555, 'PRO_REORDEN': Decimal('0.00'), 'PRO_NOMBRE': 'DESTORNILLADOR TRIA P3 X 6" GOLPE [1555]', 'IDSUBGRUPO': 5, 'PRO_MODDESCRIPCION': 1, 'PRO_TIPOEXISTENCIA': None, 'ESPECIAL': None, 'PRO_ATE1': Decimal('19.99'), 'PRO_ATE2': None, 'IDCOMPANIA': 1, 'DESCRIPCION': 'golpe.jpg', 'DESCRIPCION_CORTA': Decimal('-100.00'), 'PRO_ITBIS': 'True', 'PRO_COSTORD': Decimal('46.62')}
    SQL_PRODUCTOS = "insert into product_template (id, warranty, supply_method, uos_id, list_price,            weight, standard_price,        mes_type,  uom_id,  description_purchase, uos_coeff, sale_ok, purchase_ok, product_manager, company_id, state, loc_rack, uom_po_id, type,      description,           weight_net, volume, description_sale, procure_method,  cost_method, loc_row, name,                 rental,  sale_delay, loc_case, produce_delay, categ_id, create_uid, create_date, write_uid, write_date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    SQL_PRODUCTOS_DATA = (                         id, 0.0,      'buy',         None,   produc["PRO_PRECIO2"], '0.00', produc["PRO_COSTORD"], 'fixed',   1,       None,                 '1.000',   'True',  'True',      None,            1,          None,  None,     1,         'product', produc["DESCRIPCION"], '0.00',     0.0,    None,             'make_to_stock', 'average',   None,    produc["PRO_NOMBRE"], 'False', 7.0,        None,     1.0,           1,        1,          None,        1,         None)
    cur.execute(SQL_PRODUCTOS, SQL_PRODUCTOS_DATA)

    # insert into product_supplier_taxes_rel (prod_id,tax_id) values (17841, 6)
    product_supplier_taxes_rel = "insert into product_supplier_taxes_rel (prod_id,tax_id) values (%s, %s)"
    product_supplier_taxes_rel_data = (id, 6)
    cur.execute(product_supplier_taxes_rel, product_supplier_taxes_rel_data)

    # insert into product_taxes_rel (prod_id,tax_id) values (17841, 10)
    product_taxes_rel = "insert into product_taxes_rel (prod_id,tax_id) values (%s, %s)"
    product_taxes_rel_data = (id, 10)
    cur.execute(product_taxes_rel, product_taxes_rel_data)

    product_product = "INSERT INTO product_product (product_tmpl_id, default_code, active, valuation,         image,                        available_in_pos, image_small,                    image_medium,                    pos_categ_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    product_product_data = (                        id,              id,           True,   'manual_periodic', img_big,                      True,              img_med,                     img_med,                       1)
    cur.execute(product_product, product_product_data)
    print count
    if count == 100:
        conn.commit()
        count = 0
        print "commit()"


conn.commit()
cur.close()
conn.close()