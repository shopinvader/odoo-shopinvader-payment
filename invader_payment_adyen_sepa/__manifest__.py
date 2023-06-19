# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Invader Payment Adyen - Sepa",
    "summary": """Manage SEPA payment by Adyen""",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "depends": [
        "invader_payment_adyen",
        "account_banking_sepa_direct_debit",
        "base_iban",
        "queue_job",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/account_payment_order.xml",
        "views/account_payment_method.xml",
    ],
    "external_dependencies": {"python": ["Adyen"]},
}
