# Copyright Odoo SA (https://odoo.com)
# Copyright 2025 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import urljoin

from werkzeug import urls

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _worldline_create_checkout_session(self):
        if self.env.context.get("shopinvader_api_payment"):
            shopinvader_api_payment_base_url = self.env.context.get(
                "shopinvader_api_payment_base_url"
            )
            return_url = urljoin(shopinvader_api_payment_base_url, "worldline/return")
            return_url_params = urls.url_encode(
                {"provider_id": str(self.provider_id.id)}
            )
            self = self.with_context(
                shopinvader_api_payment_worldline_return_url=(
                    f"{return_url}?{return_url_params}"
                )
            )

        return super()._worldline_create_checkout_session()
