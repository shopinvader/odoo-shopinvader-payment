# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Rest Payment Stripe",
    "description": """
        Stripe payment with rest api""",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV",
    "website": "https://acsone.eu/",
    "depends": ["component", "base_rest", "payment_stripe", "rest_payment"],
    "data": [],
    "demo": [],
    "external_dependencies": {"python": ["stripe"]},
}
