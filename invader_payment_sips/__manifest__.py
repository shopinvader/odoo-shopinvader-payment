# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "SIPS Payment Acquirer (REST, Base)",
    "summary": "REST Services for Worldline SIPS Payments (base module)",
    "version": "13.0.1.0.0",
    "author": "ACSONE SA/NV",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "license": "AGPL-3",
    "category": "e-commerce",
    "depends": ["invader_payment", "payment_sips", "base_rest"],
    "external_dependencies": {"python": ["cerberus"]},
    "installable": True,
}
