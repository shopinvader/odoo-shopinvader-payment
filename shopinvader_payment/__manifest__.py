# Copyright 2017 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopinvader Payment",
    "summary": "Payment integration for Shopinvader",
    "version": "14.0.1.2.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "Akretion",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["cerberus", "unidecode"], "bin": []},
    "depends": [
        "shopinvader",
        "onchange_helper",
        "invader_payment",
        "component_event",
    ],
    "data": [
        "views/shopinvader_menu.xml",
        "views/shopinvader_payment_view.xml",
        "views/backend_view.xml",
        "security/security.xml",
    ],
}
