# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Shopinvader invoice payment",
    "summary": "Invoice payment integration for Shopinvader",
    "author": "ACSONE SA/NV",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "category": "e-commerce",
    "version": "14.0.1.0.3",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus", "unidecode"]},
    "depends": [
        "onchange_helper",
        "account_payment_partner",
        "shopinvader_payment",
        "shopinvader_invoice",
        "component_event",
        "invader_invoice_payment",
    ],
}
