# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Shopinvader invoice payment",
    "summary": """Invoice payment integration for Shopinvader""",
    "author": "ACSONE SA/NV",
    "website": "http://acsone.eu",
    "category": "e-commerce",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus", "unidecode"], "bin": []},
    "depends": [
        "onchange_helper",
        "account_payment_partner",
        "shopinvader_payment",
        "shopinvader_invoice",
        "component_event",
        "invader_invoice_payment",
        "shopinvader_payment_manual",
    ],
    "data": [],
    "demo": [],
}
