# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    shopinvader_frontend_redirect_url = fields.Char(
        string="Shopinvader Frontend Redirect URL",
        help="URL where the frontend should be redirected after the payment processing",
    )
