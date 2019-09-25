# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopinvader Payment Manual",
    "summary": """
        REST Services for manual payment (like bank transfer, check...)""",
    "version": "10.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "invader_payment_manual",
        "shopinvader_payment",
        "payment_transfer",
    ],
    "demo": ["demo/payment_demo.xml"],
    "autoinstall": True,
    "installable": True,
}
