# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Invader invoice payement",
    "summary": "Invader addon to make invoice payment",
    "author": "ACSONE SA/NV",
    "website": "https://github.com/shopinvader/odoo-shopinvader-payment",
    "category": "e-commerce",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "depends": ["account", "payment", "onchange_helper", "invader_payment"],
    "data": ["views/account_move.xml"],
}
