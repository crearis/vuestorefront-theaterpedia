# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# extended 2024 by theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Vue Storefront Api',
    'version': '16.0.1.0.0',
    'summary': 'Vue Storefront API',
    'description': """Vue Storefront API Integration, extended for theaterpedia.org""",
    'category': 'Website',
    'license': 'LGPL-3',
    'author': 'OdooGap',
    'website': 'https://www.odoogap.com/',
    'depends': [
        'graphql_base',
        'website_sale_wishlist',
        'website_sale_delivery',
        'website_mass_mailing',
        'website_sale_loyalty',
        'auth_signup',
        'contacts',
        'crm',
        'theme_default',
        'payment_adyen_vsf',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'data/mail_template.xml',
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'views/product_views.xml',
        'views/website_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'data/demo_product_attribute.xml',
        'data/demo_product_public_category.xml',
        'data/demo_products_women_clothing.xml',
        'data/demo_products_women_shoes.xml',
        'data/demo_products_women_bags.xml',
        'data/demo_products_men_clothing_1.xml',
        'data/demo_products_men_clothing_2.xml',
        'data/demo_products_men_clothing_3.xml',
        'data/demo_products_men_clothing_4.xml',
        'data/demo_products_men_shoes.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook_login_check',
    'post_init_hook': 'post_init_hook_login_convert',
}
