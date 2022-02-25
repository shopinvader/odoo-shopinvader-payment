# Copyright 2021 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "shopinvader_payment_gift_card",
    "summary": "Shopinvader Services for Gift Cards and Payments with",
    "version": "14.0.1.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "shopinvader_payment",
        "shopinvader_gift_card",
        "account_payment_gift_card",
        "base_rest",
        "base_jsonify",
        "base_rest_datamodel",
        "shopinvader_payment_manual",
    ],
}
