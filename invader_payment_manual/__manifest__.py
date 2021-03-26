# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Manual",
    "summary": """
        REST Services for manual payment like bank transfer,
        check ... (base module)""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": ["invader_payment", "base_rest", "payment_transfer"],
    "external_dependencies": {"python": ["cerberus"]},
    "data": ["data/payment_acquirer_data.xml"],
    "installable": True,
}
