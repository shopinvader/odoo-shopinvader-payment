# Copyright Odoo SA (https://odoo.com)
# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import quote_plus, urljoin

from odoo import models


class PaymentTransactionStripe(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_processing_values(self, processing_values):
        shopinvader_api_payment = self.env.context.get("shopinvader_api_payment")

        rv = super()._get_specific_processing_values(processing_values)
        if not shopinvader_api_payment or self.provider_code != "stripe":
            return rv

        shopinvader_api_payment_frontend_redirect_url = (
            self.shopinvader_frontend_redirect_url
        )
        shopinvader_api_payment_base_url = self.env.context.get(
            "shopinvader_api_payment_base_url"
        )
        rv["return_url"] = (
            f"{urljoin(shopinvader_api_payment_base_url, 'stripe/checkout_return')}"
            f"?reference={quote_plus(self.reference)}"
            f"&redirect_url={quote_plus(shopinvader_api_payment_frontend_redirect_url)}"
        )
        return rv
