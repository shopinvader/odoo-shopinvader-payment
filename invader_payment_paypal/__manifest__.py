# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Paypal Payment Acquirer (REST, Base)",
    "summary": "REST Services for Stripe Payments (base module)",
    "version": "12.0.1.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "Akretion",
    "license": "AGPL-3",
    "external_dependencies": {
        "python": ["cerberus", "paypalrestsdk"],
        "bin": [],
    },
    "depends": ["invader_payment", "payment_paypal", "base_rest"],
    "demo": ["demo/payment_demo.xml"],
    "data": ["views/payment_acquirer_view.xml"],
}
