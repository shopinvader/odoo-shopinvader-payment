#  Copyright 2022 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Shopinvader REST Services for list payment methods (REST, Base)",
    "summary": "REST Services list of payment methods (base module).",
    "version": "14.0.0.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "KMEE INFORMATICA LTDA",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus"]},
    "depends": [
        "account_payment_mode",
        "invader_payment",
        "base_rest",
    ],
    "demo": [],
    "data": [
        "views/account_payment_method.xml",
    ],
}
