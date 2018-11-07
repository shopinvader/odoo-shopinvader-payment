# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import pprint

from odoo import _
from odoo.addons.base_rest.components.service import (
    skip_secure_params,
    skip_secure_response,
)
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import MissingError
from odoo.http import request

_logger = logging.getLogger(__name__)


class StripeService(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "stripe.service"
    _description = """
            Allow to use the stripe payment service
        """

    # In a component, not a model (super().create not existent)
    # pylint: disable=method-required-super
    def create(self, tx_id, token, return_url):
        """
        Create the Stripe payment
        :param tx_id: the odoo transaction id (payment.transaction)
        :param token: the stripe source (get by stripe.createSource in js side)
        :param return_url: the path to return when succeed (with domain)
        :param cancel_url: the path to return when canceled (with domain)
        :return: the return_url param or the one provided by stripe
            (in case of 3d secure, stripe will redirect to return_url after)
        """
        # This method is inspirited by the /payment/stripe/create_charge route
        # in the payment_stripe addon (with adding the 3d secure)

        TX = request.env["payment.transaction"]
        tx = TX.browse(tx_id)
        if not tx:
            raise MissingError(_("Unknown transaction"))

        response = tx._create_stripe_3d_secure(
            token["id"], token["email"], return_url
        )
        if not response:
            response = tx._create_stripe_charge(
                tokenid=token["id"], email=token["email"]
            )
        elif response.get("redirect", {}).get("url"):
            return_url = response.get("redirect", {}).get("url")
        _logger.info(
            "Stripe: entering form_feedback with post data %s",
            pprint.pformat(response),
        )
        if response:
            request.env["payment.transaction"].sudo().with_context(
                lang=None
            ).form_feedback(response, "stripe")
        return {"redirect_to": return_url}

    def _validator_create(self):
        return {
            "tx_id": {"type": "integer", "coerce": int},
            "return_url": {"type": "string"},
            "token": {
                "type": "dict",
                "schema": {
                    "id": {"type": "string"},
                    "email": {"type": "string"},
                },
            },
        }

    def _validator_return_create(self):
        return {"redirect_to": {"type": "string"}}

    # the params is a huge json
    @skip_secure_params
    # stripe wait only the HTTP 200 code status (no json response)
    @skip_secure_response
    def webhook(self, **payload):
        """
        Handle stripe webhook
        :param payload: stripe event value
        :return: nothing (stripe wait for HTTP 200)
        """
        source = payload["data"]["object"]["metadata"]["reference"]
        transaction = self.env["payment.transaction"].search(
            [("reference", "=", source)]
        )

        if transaction:
            transaction._stripe_process_webhook(payload)
        if not transaction:
            raise MissingError(_("Unknown transaction"))

    def _validator_webhook(self):
        # needed for swagger
        return {}

    def _validator_return_webhook(self):
        # needed for swagger
        return {}
