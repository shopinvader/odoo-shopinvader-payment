# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    def _worldline_make_request(
        self, endpoint, payload=None, method="POST", idempotency_key=None
    ):
        # We hook here to insert shopinvader specific urls since the
        # payment.transaction._worldline_create_checkout_session does not allow
        # payload override.

        return_url = self.env.context.get(
            "shopinvader_api_payment_worldline_return_url"
        )
        if return_url and payload:
            if "hostedCheckoutSpecificInput" in payload:
                payload["hostedCheckoutSpecificInput"]["returnUrl"] = return_url
            if "redirectPaymentMethodSpecificInput" in payload:
                payload["redirectPaymentMethodSpecificInput"]["redirectionData"][
                    "returnUrl"
                ] = return_url

        return super()._worldline_make_request(
            endpoint, payload=payload, method=method, idempotency_key=idempotency_key
        )
