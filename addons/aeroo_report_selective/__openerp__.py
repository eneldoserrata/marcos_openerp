# -*- coding: utf-8 -*-
{
    'name' : 'Aeroo report selective',
    'version' : '1.0.0',
    'category' : 'Sales',
    'author' : 'Proxiad',
    'summary' : 'Aeroo reports with custom style for specific products',
    'description' :
"""
Print products with custom styles in your reports.
====================================================

Summary
----------------------------------------------------

This module provides:

    - A new menu in Settings/Aeroo Reports/Aeroo product template:
        This new page provides a way for administrator to add print categories. These categories
        will be attached to products.
    - A new field in Product view, tab "Aeroo" -> Aeroo report category
    - A custom parser:
        This is where all is done. Basically, it will exposes a new method to aeroo reports:

            **get_by_categories(resource_type, id)**

        where
            - **resource_type**: account.invoice or sale.order (needed to retrieve appropriate lines)
            - **id**: is the resource id, basically, it's the o.id member.

        This method returns a list of product categories, each category containing the following properties:

            - **sequence**: Priority for this category as set in the aeroo product template page
            - **name**: Name of the category
            - **code**: Code for this category
            - **lines**: Contains invoice_line or order_line depending on the resource_type
            - **discount**: Total discount for this category
            - **total**: Total without Taxes for this category
    - Two samples:
        - Sample invoice selective: Sample invoice report using the new functionality
        - Sample order selective: Sample order report using the new functionality

        You can use them as a starting point to make your own reports!


How to use the parser in your own reports
----------------------------------------------------

Create your report in Settings/Aeroo Reports/Reports as you used to. In the tab "Parser", set "State of Parser" to "Location"
and "Parser location" to "aeroo_report_selective/report/selective_parser.py".

Now, you should be able to use the **get_by_categories** method in your own report and start customizing it!

""",
    'depends' : [
        'report_aeroo',
        'sale'
    ],
    'data' : [
        'security/ir.model.access.csv',
        'aeroo_product_template_view.xml',
        'product_view.xml',
        'report/sample_report_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}