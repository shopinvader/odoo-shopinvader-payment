#  Copyright 2022 KMEE
# @author Cristiano Rodrigues <cristiano.rodrigues@kmee.com.br>
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Pagseguro Payment Acquirer (REST, Base)",
    "summary": "REST Services for Pagseguro Payments (base module)",
    "version": "14.0.0.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "KMEE INFORMATICA LTDA",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus"]},
    "depends": [
        "account_payment_mode",
        "invader_payment",
        "payment_pagseguro",
        "base_rest",
    ],
    "demo": ["demo/res_partner.xml"],
    "data": [
        "data/payment_method_data.xml",
        "data/payment_mode.xml",
    ],
}
