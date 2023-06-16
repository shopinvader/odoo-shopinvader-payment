# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Adyen - Klarna capture payment at delivery",
    "summary": "Klarna payment mode - Capture payment during Picking out validation",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "stock",
        "invader_payment_adyen_klarna_capture",
        "invader_payment_adyen_klarna_sale",
    ],
    "data": [
        "wizards/adyen_klarna_capture_manual.xml",
    ],
}
