# -*- coding: utf-8 -*-
{
    'name': "freight",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product',],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/wizard_do_views.xml',
        'views/wizard_do_cancel_view.xml',
        'views/wizard_print_rekap_do_view.xml',
        'views/wizard_print_rekap_create_do_view.xml',
        'views/wizard_print_rekap_do_unused_view.xml',
        'views/wizard_print_rekap_shift_view.xml',
        'views/web_asset_backend_template.xml',
        'views/wizard_user_status_view.xml',
		'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        "static/src/xml/attendance.xml",
    ],
}

