# -*- encoding: utf-8 -*-

{
    "name": "Marcos Conciliation",
    "version": "1.0",
    "description": """
        TODO
    """,
    "author": "Marcos Organizador de Negocios",
    "website": "http://marcos.do",
    "category": "Financial",
    "depends": [
        "base",
        "account",
        "account_voucher",
        "point_of_sale"
        ],
    "data":["data/account_conciliation_data.xml",
            "security/account_conciliation_security.xml",
            "security/ir.model.access.csv",
            "views/account_conciliation_view.xml",
            "views/account_view.xml",
            "workflow/account_conciliation_workflow.xml"
            ],
    "demo_xml": [],
    "update_xml": [],
    "active": False,
    "installable": True,
    "certificate": "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
