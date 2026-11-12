# Copyright Odoo SA (https://odoo.com)
# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import pprint
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from odoo.addons.payment_stripe.controllers.main import (
    StripeController as OdooStripeController,
)
from odoo.addons.shopinvader_api_payment.routers import payment_router
from odoo.addons.shopinvader_api_payment.routers.payment import (
    PaymentHelper,
    payment_helper,
)
from odoo.addons.shopinvader_api_payment.routers.utils import (
    add_query_params_in_url,
    tx_state_to_redirect_status,
)

_logger = logging.getLogger(__name__)


@payment_router.get("/payment/providers/stripe/checkout_return")
def stripe_return_from_checkout(
    request: Request,
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
) -> RedirectResponse:
    """Process the notification data sent by Stripe after redirection from checkout.

    From Odoo payment_stripe /payment/stripe/checkout_return route.
    """
    # convert QueryParam to dict so it is mutable, because
    # _include_payment_intent_in_notification_data wants to mutate it.
    data = dict(request.query_params)

    # Retrieve the tx based on the tx reference included in the return url
    tx_sudo = helper._get_tx_from_notification_data("stripe", data)

    if tx_sudo.operation != "validation":
        # Fetch the PaymentIntent and PaymentMethod objects from Stripe.
        payment_intent = tx_sudo.provider_id._stripe_make_request(
            f"payment_intents/{data.get('payment_intent')}",
            payload={"expand[]": "payment_method"},  # Expand all required objects.
            method="GET",
        )
        secret_keys = tx_sudo._get_specific_secret_keys()
        logged_intent = {
            k: v for k, v in payment_intent.items() if k not in secret_keys
        }
        _logger.info(
            "Received payment_intents response:\n%s", pprint.pformat(logged_intent)
        )
        OdooStripeController._include_payment_intent_in_notification_data(
            payment_intent, data
        )
    else:
        # Fetch the SetupIntent and PaymentMethod objects from Stripe.
        setup_intent = tx_sudo.provider_id._stripe_make_request(
            f"setup_intents/{data.get('setup_intent')}",
            payload={"expand[]": "payment_method"},  # Expand all required objects.
            method="GET",
        )
        _logger.info(
            "Received setup_intents response:\n%s", pprint.pformat(setup_intent)
        )
        OdooStripeController._include_setup_intent_in_notification_data(
            setup_intent, data
        )

    # Handle the notification data crafted with Stripe API's objects.
    tx_sudo._handle_notification_data("stripe", data)

    # Redirect the user to the status page
    status = tx_state_to_redirect_status(tx_sudo.state)
    tx_reference = data.get("reference", "")
    redirect_url = data.get("redirect_url", "")
    return RedirectResponse(
        url=add_query_params_in_url(
            redirect_url, {"status": status, "reference": quote_plus(tx_reference)}
        ),
        status_code=303,
    )
