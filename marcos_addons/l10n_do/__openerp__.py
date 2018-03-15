# -*- encoding: utf-8 -*-
{
    'name': 'Contabilidad República Dominicana',
    'category': 'Localization/Account Charts',
    'version': '1.0',
    'url': '',
    'author': '',
    'website': '',
    'description': """

    """,
    'depends': ['account', 'account_chart', 'base', 'sale'],
    'init_xml': [],
    'data_xml': [],
    'update_xml': [
        'l10n_do_base_data.xml',
        'data/ir_sequence_type.xml',
        'data/ir_sequence.xml',
        'data/account_account_template.xml',
        'data/account_account_template_eym.xml',
        'data/account_tax_code_template.xml',
        'data/account_chart_template.xml',
        # 'data/account_tax_template.xml',
        'data/account_tax_template_eym.xml',
        'data/account_journal.xml',
        'data/ncf_data_init.xml',
        'l10n_wizard.xml'
    ],
    'license': 'Other OSI approved licence',
    'installable': True,
    'auto_install': False,
    'certificate' : '',
    'images': ['images/config_chart_l10n_do.jpeg','images/l10n_do_chart.jpeg'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
