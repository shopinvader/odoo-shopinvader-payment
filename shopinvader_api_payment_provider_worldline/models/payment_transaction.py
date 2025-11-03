# Copyright Odoo SA (https://odoo.com)
# Copyright 2025 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import urljoin

from werkzeug import urls

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _worldline_create_checkout_session_get_payload(self):
        self.ensure_one()
        payload = super()._worldline_create_checkout_session_get_payload()
        if not self.env.context.get("shopinvader_api_payment"):
            return payload
        shopinvader_api_base_url = self.shopinvader_frontend_redirect_url
        return_url = urljoin(
            shopinvader_api_base_url, "/shopinvader/payment/providers/worldline/return"
        )
        return_url_params = urls.url_encode({"provider_id": str(self.provider_id.id)})
        payload["hostedCheckoutSpecificInput"][
            "returnUrl"
        ] = f"{return_url}?{return_url_params}"
        return payload
