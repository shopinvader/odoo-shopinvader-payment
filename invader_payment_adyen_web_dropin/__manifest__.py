# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Adyen Web drop-in",
    "summary": "Adds a new payment service for Adyen Web drop-in",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "invader_payment_adyen_abstract",
        "base_rest",
        "invader_payment_sale",
    ],
    "data": [
        "data/decimal_precision.xml",
        "data/payment_acquirer.xml",
        "data/job_channel.xml",
        "data/job_function.xml",
        "views/payment_acquirer.xml",
    ],
    "external_dependencies": {"python": ["cerberus", "Adyen"]},
}
