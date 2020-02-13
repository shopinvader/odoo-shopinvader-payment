# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import stripe
from odoo import _
from odoo.addons.base_rest.components.service import (
    skip_secure_params,
    skip_secure_response,
)
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)


class WebhookServiceStripe(AbstractComponent):

    _inherit = "base.rest.service"
    _name = "webhook.service.stripe"
    _description = """
    Webhook for stripe
    """

    # the params is a huge json
    @skip_secure_params
    # stripe wait only the HTTP 200 code status (no json response)
    @skip_secure_response
    def create(self, **payload):
        """
        Endpoint called by stripe. It must be in public auth
        Useful in case of a customer leaving the page before the redirection
        is done
        :param payload: stripe event value
        :return: nothing (stripe wait for HTTP 200)
        """
        source = (
            payload.get("data", {})
            .get("object", {})
            .get("metadata", {})
            .get("reference")
        )
        if not source:
            _logger.info(
                "Webhook of type %s without reference: ignored",
                payload.get("type"),
            )
            return
        transaction = self.env["payment.transaction"].search(
            [("acquirer_reference", "=", source)]
        )
        if not transaction:
            raise MissingError(
                _(
                    "Source {} not found in the transaction. "
                    "It was perhaps already paid."
                )
            )
        if transaction.state != "pending":
            # already took care synchronously
            return

        api_key = transaction.acquirer_id.stripe_secret_key
        event = stripe.Event.construct_from(payload, api_key)
        self._consume_webhook(event, transaction)

    def _get_webhook_handler(self):
        return {
            "source.chargeable": self._stripe_process_source_chargeable,
            "source.canceled": self._stripe_process_source_canceled,
            "source.failed": self._stripe_process_source_failed,
        }

    def _consume_webhook(self, event, transaction):
        handler = self._get_webhook_handler().get(event.type)
        if handler:
            handler(event, transaction)

    def _stripe_process_source_chargeable(self, event, transaction):
        transaction.charge_source()

    def _stripe_process_source_canceled(self, event, transaction):
        transaction.state = "cancel"

    def _stripe_process_source_failed(self, event, transaction):
        transaction.state = "error"
