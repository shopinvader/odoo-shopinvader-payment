# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopinvader Api Payment Provider Monetico",
    "summary": "Specific routes for monetico payments from Shopinvader",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "Shopinvader, Akretion",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "fastapi",
        "shopinvader_api_payment",
        "payment_monetico",
    ],
    "data": [],
    "installable": True,
}
