# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Stripe Bancontact",
    "summary": """
        REST Services for Stripe Bancontact Payments (base module)""",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://acsone.eu/",
    "depends": ["payment_stripe", "invader_payment_stripe_charge"],
    "data": ["views/payment_acquirer.xml"],
    "demo": [],
}
