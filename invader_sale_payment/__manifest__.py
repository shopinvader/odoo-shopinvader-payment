# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Sale Payment",
    "summary": """
        Backport the model definition between payment.transaction and
        sale.order""",
    "version": "10.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV",
    "website": "https://acsone.eu/",
    "depends": ["sale", "payment"],
    "data": ["views/sale_order.xml", "views/payment_transaction.xml"],
    "demo": [],
    "installable": True,
}
