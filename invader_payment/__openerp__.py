# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopinvader Payment",
    "summary": "Payment integration for Shopinvader",
    "version": "9.0.1.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "ACSONE SA/NV",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["cerberus", "unidecode"], "bin": []},
    "depends": ["payment", "account_payment_mode"],
    "data": ["views/account_payment_mode.xml"],
}
