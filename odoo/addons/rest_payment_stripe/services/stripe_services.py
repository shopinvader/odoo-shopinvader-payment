# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import pprint

from odoo import _
from odoo.addons.component.core import AbstractComponent
from odoo.http import request
from odoo.exceptions import MissingError, ValidationError

_logger = logging.getLogger(__name__)


class StripeService(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "stripe.service"
    _description = """
            Allow to use the stripe payment service
        """

    # In a component, not a model (super().create not existent)
    # pylint: disable=method-required-super
    def create(self, tx_id, payment_method_id=False, payment_intent_id=False):
        """
        Create the Stripe payment
        :param tx_id: the odoo transaction id (payment.transaction)
        :param payment_method_id: the stripe payment method
            (get by stripe.createPaymentMethod in js side)
        :param payment_intent_id: the stripe payment intent
            (returned in the paylaod when calling with payment_method_id)
        :return: the return_url param or the one provided by stripe
            (in case of 3d secure, stripe will redirect to return_url after)
        """
        # This method is inspirited by the /payment/stripe/create_charge route
        # in the payment_stripe addon (with adding the 3d secure)

        TX = request.env["payment.transaction"]
        tx = TX.browse(tx_id)
        if not tx:
            raise MissingError(_("Unknown transaction"))

        intent = tx._create_stripe_3d_secure(
            payment_method_id=payment_method_id,
            payment_intent_id=payment_intent_id)
        if intent.status == 'requires_action' and \
                intent.next_action.type == 'use_stripe_sdk':
            return {
                "size": "aa",
                "data": {
                    "status": "requires_action",
                    "payload": intent.client_secret,
                }}
        if intent.status == 'succeeded':
            _logger.info('Stripe: entering form_feedback with post data %s',
                         pprint.pformat(intent))
            request.env['payment.transaction'].sudo().with_context(
                lang=None).form_feedback(intent, 'stripe')
            return {"data": {"status": "success"}, "size": "aa"}
        raise ValidationError(_("Sorry, something gone wrong"))

    def _validator_create(self):
        return {
            "tx_id": {
                "type": "integer",
                "coerce": int,
            },
            "payment_method_id": {
                "type": "string",
            },
            "payment_intent_id": {
                "type": "string",
            },
        }

    def _validator_return_create(self):
        return {
            "data": {
                "type": "dict",
                "schema": {
                    "status": {
                        "type": "string",
                    },
                    "payload": {
                        "type": "string",
                    },
                },
            },
            "size": {  # DUMMY!!!
                "type": "string",
            },
        }
