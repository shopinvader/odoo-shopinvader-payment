# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stripe Payment Acquirer (REST, Base)",
    "summary": "REST Services for Stripe Payments (base module)",
    "version": "12.0.2.1.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "ACSONE SA/NV",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus", "stripe"], "bin": []},
    "depends": ["invader_payment", "payment_stripe", "base_rest"],
    "demo": ["demo/payment_demo.xml"],
}
