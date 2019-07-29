# Copyright 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopinvader Payment Stripe",
    "summary": "Shopinvader Stripe Payment",
    "version": "12.0.1.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "Akretion, ACSONE SA/NV",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": True,
    "external_dependencies": {"python": ["stripe"], "bin": []},
    "depends": ["shopinvader_payment", "payment_stripe"],
}
