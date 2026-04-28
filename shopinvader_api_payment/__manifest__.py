# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopinvader Api Payment",
    "summary": "Shopinvader services to be able to pay (invoices, carts,...)",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Shopinvader",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "payment",
        "shopinvader_router_helper",
        "extendable_fastapi",
    ],
    "external_dependencies": {
        "python": [
            "pyjwt",
        ],
    },
    "installable": True,
}
