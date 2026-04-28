# Copyright Odoo SA (https://odoo.com)
# Copyright 2025 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from werkzeug.exceptions import Forbidden

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.payment_worldline.controllers.main import WorldlineController
from odoo.addons.shopinvader_api_payment.routers import payment_router
from odoo.addons.shopinvader_api_payment.routers.payment import payment_helper
from odoo.addons.shopinvader_api_payment.routers.utils import (
    add_query_params_in_url,
    tx_state_to_redirect_status,
)
from odoo.addons.shopinvader_router_helper import VirtualModel

_logger = logging.getLogger(__name__)


class PaymentHelper(VirtualModel):
    _inherit = "shopinvader_api_payment.payment_router.helper"

    def _verify_worldline_signature(self, tx_sudo, received_signature, data):
        """Verify the Worldline signature."""
        try:
            WorldlineController._verify_notification_signature(
                data, received_signature, tx_sudo
            )
        except Forbidden as ex:
            _logger.exception(ex)
            raise ValidationError(_("Unable to verify worldline signature")) from ex


@payment_router.get("/payment/providers/worldline/return")
async def worldline_return(
    request: Request,
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
) -> RedirectResponse:
    """Handle SIPS return.

    After the payment, the user is redirected with a POST to this endpoint. We handle
    the notification data to update the transaction status. We then redirect the browser
    with a GET to the frontend_return_url, with the transaction reference as parameter.

    Future: we could also return a unguessable transaction uuid that the front could the
    use to consult /payment/transactions/{uuid} and obtain the transaction status.
    """
    data = await request.form()
    _logger.info(
        "return notification received from Worldline with data:\n%s",
        pprint.pformat(data),
    )
    params = request.query_params
    hosted_checkout_id = params.get("hostedCheckoutId")
    provider_id = int(params.get("provider_id", 0))

    provider = helper.env["payment.provider"].sudo().browse(provider_id).exists()
    if not provider or provider.code != "worldline":
        _logger.warning("Received payment data with invalid provider id.")
        raise Forbidden()

    checkout_session_data = provider._worldline_make_request(
        f"hostedcheckouts/{hosted_checkout_id}", method="GET"
    )
    _logger.info(
        "Response of '/hostedcheckouts/<hostedCheckoutId>' request:\n%s",
        pprint.pformat(checkout_session_data),
    )
    notification_data = checkout_session_data.get("createdPaymentOutput", {})

    tx_sudo = helper._get_tx_from_notification_data("worldline", notification_data)

    reference = tx_sudo.display_name
    frontend_redirect_url = tx_sudo.shopinvader_frontend_redirect_url
    try:
        tx_sudo._handle_notification_data("worldline", notification_data)
        status = tx_state_to_redirect_status(tx_sudo.state)
    except Exception:
        _logger.exception("unable to handle worldline notification data", exc_info=True)
        status = "error"
    return RedirectResponse(
        url=add_query_params_in_url(
            frontend_redirect_url,
            {"status": status, "reference": quote_plus(reference)},
        ),
        status_code=303,
    )


@payment_router.post("/payment/providers/worldline/webhook")
async def worldline_webhook(
    request: Request,
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
):
    """Handle Wordline webhook."""
    data = await request.json()
    _logger.info(
        "webhook notification received from SIPS with data:\n%s", pprint.pformat(data)
    )
    try:
        tx_sudo = helper._get_tx_from_notification_data("worldline", data)
        received_signature = request.headers.get("X-GCS-Signature")
        body = await request.body()
        helper._verify_worldline_signature(tx_sudo, received_signature, body)
        tx_sudo._handle_notification_data("worldline", data)
    except Exception:
        _logger.exception("unable to handle worldline notification data", exc_info=True)
    return ""
