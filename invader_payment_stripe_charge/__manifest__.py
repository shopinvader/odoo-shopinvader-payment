# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Stripe Charge",
    "summary": """
        Allow to use the source/charge api of stripe""",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://acsone.eu/",
    "depends": ["invader_payment_stripe"],
    "data": [],
    "demo": [],
    "external_dependencies": {"python": ["stripe"], "bin": []},
}
