# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Invader invoice payement",
    "summary": """Invader addon to make invoice payment""",
    "author": "ACSONE SA/NV",
    "website": "http://acsone.eu",
    "category": "e-commerce",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account", "payment"],
    "data": ["views/account_invoice.xml", "views/payment_transaction.xml"],
}
