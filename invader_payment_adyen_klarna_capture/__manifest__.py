# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Adyen - Klarna capture payment",
    "summary": "Klarna payment mode - Capture payment",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": ["invader_payment_adyen_klarna", "queue_job"],
    "data": [
        "security/ir_model_access.xml",
        "wizards/adyen_klarna_capture_manual.xml",
    ],
}
