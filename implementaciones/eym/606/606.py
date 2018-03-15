# -*- encoding: utf-8 -*-
import locale
import csv
from pprint import pprint as pp
locale.setlocale(locale.LC_ALL, '')

type_name = {'01': u'01 - Gastos de personal',
             '02': u'02 - Gastos por trabajo suministros y servicios',
             '03': u'03 - Arrendamientos',
             '04': u'04 - Gastos de Activos Fijos',
             '05': u'05 - Gastos de Representacion',
             '06': u'06 - Otras Deducciones Admitidas',
             '07': u'07 - Gastos Financieros',
             '08': u'08 - Gastos Extraordinarios',
             '09': u'09 - Compras y Gastos que forman parte del Costo de Venta',
             '10': u'10 - Adquisiciones de Activos',
             '11': u'11 - Gastos de Seguro'
    }
type = {'01': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '02': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '03': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '04': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '05': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '06': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '07': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '08': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '09': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '10': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
        '11': {"name": "", "itbis": 0.00, "retenido": 0.00, "facturado": 0.00},
    }

def p(value):
    return locale.currency(value, grouping=True)

mes = ['01','02','03','04','05','06','07','08','09','10','11','12']
# mes = ['08','09','10','11','12']



file_path = "/Users/eneldoserrata/PycharmProjects/marcos_openerp/implementaciones/eym/606/eymcolor2014/2014"

for m in mes:
    archi=open(file_path+m+'.txt','r')

    lineas = archi.readlines()

    count = 0.00
    for li in lineas:
        if len(li) == 50:
            continue
        tipo = li[12:14]
        nc = False
        if li[23:25] == '04':
            nc = True

        itbis = retencion = facturado = 0
        if nc:
            itbis = float(li[68:80]) * -1
            retencion = float(li[80:92]) * -1
            facturado = float(li[92:104]) * -1
        else:
            try:
                itbis = float(li[68:80])
            except:
                import pdb;pdb.set_trace()
            retencion = float(li[80:92])
            facturado = float(li[92:104])
        count += facturado

        type[tipo]["itbis"] += itbis
        type[tipo]["retenido"] += retencion
        type[tipo]["facturado"] += facturado




    print count

    type["01"].update({"name": type_name["01"]})
    type["02"].update({"name": type_name["02"]})
    type["03"].update({"name": type_name["03"]})
    type["04"].update({"name": type_name["04"]})
    type["05"].update({"name": type_name["05"]})
    type["06"].update({"name": type_name["06"]})
    type["07"].update({"name": type_name["07"]})
    type["08"].update({"name": type_name["08"]})
    type["09"].update({"name": type_name["09"]})
    type["10"].update({"name": type_name["10"]})
    type["11"].update({"name": type_name["11"]})



    with open(m+"totales.csv", 'wb') as fp:
        a = csv.writer(fp, delimiter=',')
        data = []
        data.append(["Tipo", "ITBIS", "Retenido", "Facturado"])
        data.append([type["01"]["name"], type["01"]["itbis"], type["01"]["retenido"], type["01"]["facturado"]])
        data.append([type["02"]["name"], type["02"]["itbis"], type["02"]["retenido"], type["02"]["facturado"]])
        data.append([type["03"]["name"], type["03"]["itbis"], type["03"]["retenido"], type["03"]["facturado"]])
        data.append([type["04"]["name"], type["04"]["itbis"], type["04"]["retenido"], type["04"]["facturado"]])
        data.append([type["05"]["name"], type["05"]["itbis"], type["05"]["retenido"], type["05"]["facturado"]])
        data.append([type["06"]["name"], type["06"]["itbis"], type["06"]["retenido"], type["06"]["facturado"]])
        data.append([type["07"]["name"], type["07"]["itbis"], type["07"]["retenido"], type["07"]["facturado"]])
        data.append([type["08"]["name"], type["08"]["itbis"], type["08"]["retenido"], type["08"]["facturado"]])
        data.append([type["09"]["name"], type["09"]["itbis"], type["09"]["retenido"], type["09"]["facturado"]])
        data.append([type["10"]["name"], type["10"]["itbis"], type["10"]["retenido"], type["10"]["facturado"]])
        data.append([type["11"]["name"], type["11"]["itbis"], type["11"]["retenido"], type["11"]["facturado"]])
        a.writerows(data)

    type["01"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["02"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["03"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["04"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["05"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["06"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["07"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["08"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["09"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["10"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})
    type["11"].update({"itbis": 0.00, "retenido": 0.00, "facturado": 0.00})

archi.close()