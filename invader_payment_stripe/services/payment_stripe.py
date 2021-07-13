# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import stripe
from cerberus import Validator

from odoo import _
from odoo.tools.float_utils import float_round

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.addons.payment_stripe.models.payment import INT_CURRENCIES

_logger = logging.getLogger(__name__)

# map Stripe transaction statuses to Odoo payment.transaction statuses
STRIPE_TRANSACTION_STATUSES = {
    "canceled": "cancel",
    "processing": "pending",
    "requires_action": "pending",
    "requires_capture": "authorized",
    "requires_confirmation": "pending",
    "requires_payment_method": "pending",
    "succeeded": "done",
}


class PaymentServiceStripe(AbstractComponent):

    _name = "payment.service.stripe"
    _inherit = "base.rest.service"
    _usage = "payment_stripe"
    _description = "REST Services for Stripe payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _validator_confirm_payment(self):
        """
        Validator of confirm_payment service
        target: see _allowed_payment_target()
        payment_mode_id: The payment mode used to pay
        stripe_payment_intent_id: The previously created intent
        stripe_payment_method_id: The Stripe card created on client side
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "payment_mode_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "stripe_payment_intent_id": {"type": "string"},
                "stripe_payment_method_id": {"type": "string"},
            }
        )
        return res

    def _validator_capture_payment(self):
        """
        Validator of capture_payment service
        target: see _allowed_payment_target()
        payment_mode_id: The payment mode used to pay
        stripe_payment_intent_id: The previously created intent
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "payment_mode_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "stripe_payment_intent_id": {"type": "string"},
            }
        )
        return res

    def _validator_return_confirm_payment(self):
        return Validator(
            {
                "requires_action": {"type": "boolean"},
                "payment_intent_client_secret": {"type": "string"},
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            allow_unknown=True,
        )

    def _get_formatted_amount(self, currency, amount):
        """
        The expected amount format by Stripe
        :param amount: float
        :return: int
        """
        res = int(
            amount
            if currency.name in INT_CURRENCIES
            else float_round(amount * 100, 2)
        )
        return res

    def _get_stripe_transaction_from_intent(self, intent):
        """
        Retrieve the transaction from intent string
        :param intent: string
        :return: payment.transaction
        """
        transaction = self.env["payment.transaction"].search(
            [
                ("acquirer_reference", "=", intent),
                ("acquirer_id.provider", "=", "stripe"),
            ],
            limit=1,
        )
        return transaction

    def _get_stripe_private_key(self, transaction):
        """
        Return stripe private key depending on payment.transaction recordset
        :param transaction: payment.transaction
        :return: string
        """

        acquirer = transaction.acquirer_id
        return acquirer.filtered(
            lambda a: a.provider == "stripe"
        ).stripe_secret_key

    def confirm_payment(self, target, **params):
        """
        This is the rest service exposed to locomotive and called on
        payment confirmation.
        The steps here depend on how the card is managed on Stripe side.
        * One step:
            * The stripe_payment_method_id is passed
            * The intent state is 'succeeded'
        * Two steps:
            * The stripe_payment_method_id is passed
            * The intent state is 'requires_action'
            * The stripe_payment_intent_id is passed
            * The intent state is 'succeeded'
        :param target: string (authorized value is checked by service)
        :param payment_mode_id: string (The Odoo payment mode id)
        :param stripe_payment_method_id:
        :param stripe_payment_intent_id:
        :return:
        """
        payment_mode_id = params.get("payment_mode_id")
        stripe_payment_method_id = params.get("stripe_payment_method_id")
        stripe_payment_intent_id = params.get("stripe_payment_intent_id")
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        # Stripe part
        transaction = None
        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)
        self.payment_service._check_provider(payment_mode, "stripe")

        try:
            if stripe_payment_method_id:
                # First step
                transaction = transaction_obj.create(
                    payable._invader_prepare_payment_transaction_data(
                        payment_mode
                    )
                )
                payable._invader_set_payment_mode(payment_mode)
                intent = self._prepare_stripe_intent(
                    transaction,
                    stripe_payment_method_id,
                    capture_method=self._get_stripe_capture_method(
                        payment_mode
                    ),
                )
                transaction.write({"acquirer_reference": intent.id})
            elif stripe_payment_intent_id:
                # Second step if applicable
                transaction = self._get_stripe_transaction_from_intent(
                    stripe_payment_intent_id
                )
                intent = self._confirm_stripe_intent(
                    transaction, stripe_payment_intent_id
                )
            if intent.status == "succeeded":
                # Handle post-payment fulfillment
                transaction._set_transaction_done()
            else:
                transaction.write(
                    {"state": STRIPE_TRANSACTION_STATUSES[intent.status]}
                )
            return self._generate_stripe_response(
                intent, payable, target, **params
            )

        except Exception as e:
            _logger.error("Error confirming stripe payment", exc_info=True)
            if transaction:
                # Odoo does not like to change not draft transaction to error
                transaction.write({"state": "draft"})
                transaction._set_transaction_error(
                    _("Exception: {}".format(e))
                )
            return self._generate_stripe_error_response(target, **params)

    def capture_payment(self, target, **params):
        """
        This is the rest service exposed and called on payment capture.
        :param intent_id: string representing and intent_id
        :return:
        """
        stripe_payment_intent_id = params.get("stripe_payment_intent_id")
        transaction = self._get_stripe_transaction_from_intent(
            stripe_payment_intent_id
        )
        params["transaction"] = transaction
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        try:
            intent = self._capture_stripe_intent(
                transaction, stripe_payment_intent_id
            )
            transaction.write(
                {"state": STRIPE_TRANSACTION_STATUSES[intent.status]}
            )
            return self._generate_stripe_response(
                intent, payable, target, **params
            )
        except Exception as e:
            _logger.error("Error confirming stripe payment", exc_info=True)
            if transaction:
                # Odoo does not like to change not draft transaction to error
                transaction.write({"state": "draft"})
                transaction._set_transaction_error(
                    _("Exception: {}".format(e))
                )
            return self._generate_stripe_error_response(target, **params)

    def _prepare_stripe_intent(
        self, transaction, stripe_payment_method_id, capture_method="automatic"
    ):
        """
        Prepare a StripeIntent with payment.transaction data
        :param tx_data:
        :param stripe_payment_method_id:
        :return: StripeIntent
        """
        metadata = {"reference": transaction.reference}
        currency = transaction.currency_id
        intent = stripe.PaymentIntent.create(
            payment_method=stripe_payment_method_id,
            amount=self._get_formatted_amount(currency, transaction.amount),
            currency=currency.name,
            confirmation_method="manual",
            confirm=True,
            description=transaction.reference,
            metadata=metadata,
            capture_method=capture_method,
            api_key=self._get_stripe_private_key(transaction),
        )
        return intent

    def _confirm_stripe_intent(self, transaction, stripe_payment_intent_id):
        """
        Confirm the Stripe Intent and return it
        :param stripe_payment_intent_id:
        :return: StripeIntent
        """
        return stripe.PaymentIntent.confirm(
            stripe_payment_intent_id,
            api_key=self._get_stripe_private_key(transaction),
        )

    def _capture_stripe_intent(
        self, transaction, stripe_payment_intent_id, amount=None
    ):
        """
        Capture the Stripe Intent and return it
        It is only useful if the capture method is manual
        :param stripe_payment_intent_id:
        :return: StripeIntent
        """
        return stripe.PaymentIntent.capture(
            stripe_payment_intent_id,
            api_key=self._get_stripe_private_key(transaction),
            amount_to_capture=self._get_formatted_amount(
                transaction.currency_id, amount or transaction.amount
            ),
        )

    def _generate_stripe_response(self, intent, payable, target, **params):
        """
        This is the message returned to client
        :param intent: StripeIntent (None means error)
        :param payable: invader.payable record
        :return: dict
        """
        if intent:
            if (
                intent.status == "requires_action"
                and intent.next_action.type == "use_stripe_sdk"
            ):
                # Tell the client to handle the action
                return {
                    "requires_action": True,
                    "payment_intent_client_secret": intent.client_secret,
                }
            elif (
                intent.status == "succeeded"
                or intent.status == "requires_capture"
            ):
                # The payment didn’t need any additional actions and completed!
                # If a capture is required, it is a success from the client's
                # perspetive
                return {"success": True}
            elif intent.status == "canceled":
                return {"error": _("Payment canceled.")}
            else:
                _logger.error("Unexpected intent status: %s", intent)
        return {"error": _("Payment Error")}

    def _generate_stripe_error_response(self, target, **params):
        return self._generate_stripe_response(None, None, target, **params)

    def _get_stripe_capture_method(self, payment_mode):
        if payment_mode.payment_acquirer_id.capture_manually:
            return "manual"
        else:
            return "automatic"
