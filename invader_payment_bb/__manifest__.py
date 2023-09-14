#  Copyright 2023 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Bank of Brazil Payment Acquirer (REST, Base)",
    "summary": "REST Services for Bank of Brazil Payments (base module)",
    "version": "14.0.0.0.0",
    "category": "e-commerce",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "author": "KMEE INFORMATICA LTDA",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["cerberus"]},
    "depends": ["invader_payment", "payment_bacen_pix", "base_rest"],
    "data": ["data/payment_method_data.xml", "data/payment_mode.xml"],
}
