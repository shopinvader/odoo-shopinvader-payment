# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Adyen",
    "summary": """
        Adds a new payment service for Adyen""",
    "version": "14.0.1.0.5",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": ["invader_payment", "payment_adyen_paybylink", "base_rest"],
    "maintainers": ["rousseldenis"],
    "data": [
        "data/decimal_precision.xml",
        "views/payment_acquirer.xml",
        "views/payment_transaction.xml",
    ],
    "external_dependencies": {"python": ["cerberus", "Adyen"], "bin": []},
}
