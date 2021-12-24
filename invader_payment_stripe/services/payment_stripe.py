# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import stripe
from cerberus import Validator

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

from odoo.addons.base_rest import restapi
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
    "requires_payment_method": "draft",
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

    def _validator_webhook(self):
        res = {
            "type": {"type": "string", "required": True},
            "data": {
                "type": "dict",
                "required": True,
                "schema": {
                    "object": {
                        "type": "dict",
                        "required": True,
                        "schema": {
                            "id": {"type": "string", "required": True},
                            "metadata": {
                                "type": "dict",
                                "schema": {"reference": {"type": "string"}},
                            },
                            "amount": {"type": "integer", "coerce": to_int},
                        },
                    }
                },
            },
        }
        return res

    def _validator_create(self):
        res = self.payment_service._invader_get_target_validator()
        return res

    def _validator_confirm_payment(self):
        """
        Validator of confirm_payment service
        target: see _allowed_payment_target()
        stripe_payment_intent_id: The previously created intent
        stripe_payment_method_id: The Stripe card created on client side
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "stripe_payment_intent_id": {"type": "string"},
                "stripe_payment_method_id": {"type": "string"},
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
            amount if currency.name in INT_CURRENCIES else float_round(amount * 100, 2)
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
        return acquirer.filtered(lambda a: a.provider == "stripe").stripe_secret_key

    @restapi.method(
        [(["/webhook"], "POST")],
        input_param=restapi.CerberusValidator("_validator_webhook"),
        output_param={},
    )
    def webhook(self, **event):
        acquirer = self.env.ref("payment.payment_acquirer_stripe")
        acquirer._verify_stripe_signature()
        # Handle the event
        if event and event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]  # contains a stripe.PaymentIntent
            reference = payment_intent["metadata"].get("reference")
            transaction = self.env["payment.transaction"].search(
                [("reference", "=", reference)], limit=1
            )
            if not transaction:
                raise ValidationError(
                    _(
                        "payment_intent.succeeded event received \
                            for an unknown transaction: {}, {}"
                    ).format(reference, payment_intent["id"])
                )
            _logger.info(_("Payment for {} succeeded").format(transaction.reference))
            transaction.amount = payment_intent["amount"]
            transaction._set_transaction_done()
        # elif event["type"] == "payment_method.attached":
        #    payment_method = event["data"]["object"]  # contains a stripe.PaymentMethod
        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
        else:
            # Unexpected event type
            _logger.warning("Unhandled event type {}".format(event["type"]))

    @restapi.method(
        [(["/create"], "POST")],
        input_param=restapi.CerberusValidator("_validator_create"),
        output_param=restapi.CerberusValidator("_validator_return_confirm_payment"),
    )
    # pylint: disable=W8106
    def create(self, target, **params):
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )
        acquirer = self.env.ref("payment.payment_acquirer_stripe")

        transaction = self.env["payment.transaction"].create(
            payable._invader_prepare_payment_transaction_data(acquirer)
        )
        intent = self._prepare_stripe_intent(transaction, None)
        transaction.write(
            {
                "acquirer_reference": intent.id,
                "state": STRIPE_TRANSACTION_STATUSES[intent.status],
            }
        )
        return self._generate_stripe_response(intent, payable, target, **params)

    @restapi.method(
        [(["/confirm_payment"], "POST")],
        input_param=restapi.CerberusValidator("_validator_confirm_payment"),
        output_param=restapi.CerberusValidator("_validator_return_confirm_payment"),
    )
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
        :param stripe_payment_method_id:
        :param stripe_payment_intent_id:
        :return:
        """
        stripe_payment_method_id = params.get("stripe_payment_method_id")
        stripe_payment_intent_id = params.get("stripe_payment_intent_id")
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        # Stripe part
        transaction = None
        acquirer = self.env.ref("payment.payment_acquirer_stripe")

        try:
            if stripe_payment_method_id:
                # First step
                transaction = transaction_obj.create(
                    payable._invader_prepare_payment_transaction_data(acquirer)
                )
                intent = self._prepare_stripe_intent(
                    transaction, stripe_payment_method_id
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
                transaction.write({"state": STRIPE_TRANSACTION_STATUSES[intent.status]})
            return self._generate_stripe_response(intent, payable, target, **params)

        except Exception as e:
            _logger.error("Error confirming stripe payment", exc_info=True)
            if transaction:
                # Odoo does not like to change not draft transaction to error
                transaction.write({"state": "draft"})
                transaction._set_transaction_error(_("Exception: {}".format(e)))
            return self._generate_stripe_error_response(target, **params)

    def _prepare_stripe_intent(self, transaction, stripe_payment_method_id):
        """
        Prepare a StripeIntent with payment.transaction data
        :param tx_data:
        :param stripe_payment_method_id:
        :return: StripeIntent
        """
        metadata = {"reference": transaction.reference}
        currency = transaction.currency_id
        intent_kwargs = {
            "api_key": self._get_stripe_private_key(transaction),
            "amount": self._get_formatted_amount(currency, transaction.amount),
            "currency": currency.name,
            "description": transaction.reference,
            "metadata": metadata,
        }
        # If there is no payment method, that means the initialization is done server-side
        if stripe_payment_method_id:
            intent_kwargs["payment_method"] = stripe_payment_method_id
            intent_kwargs["confirmation_method"] = "manual"
            intent_kwargs["confirm"] = True
        else:
            intent_kwargs["automatic_payment_methods"] = {"enabled": True}
        intent = stripe.PaymentIntent.create(**intent_kwargs)
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
            elif intent.status == "requires_payment_method":
                # Tell the client to handle the payment method choice
                return {
                    "requires_payment_method": True,
                    "payment_intent_client_secret": intent.client_secret,
                }
            elif intent.status == "succeeded":
                # The payment didn’t need any additional actions and completed!
                return {"success": True}
            elif intent.status == "canceled":
                return {"error": _("Payment canceled.")}
            else:
                _logger.error("Unexpected intent status: %s", intent)
        return {"error": _("Payment Error")}

    def _generate_stripe_error_response(self, target, **params):
        return self._generate_stripe_response(None, None, target, **params)
