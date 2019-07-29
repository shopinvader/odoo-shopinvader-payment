# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import stripe
from odoo.addons.component.core import Component
from odoo.addons.payment_stripe.models.payment import INT_CURRENCIES
from odoo.tools.float_utils import float_round

STRIPE_TRANSACTION_STATUSES = {
    "canceled": "cancel",
    "processing": "pending",
    "requires_action": "pending",
    "requiresauthorization": "pending",
    "requirescapture": "pending",
    "requiresconfirmation": "pending",
    "requirespaymentmethod": "pending",
    "succeeded": "done",
}


class StripeKeyManager(object):
    def __enter__(self):
        pass

    def __init__(self, stripe, api_key):
        stripe.api_key = api_key

    # pylint: disable=redefined-builtin
    def __exit__(self, type, value, traceback):
        stripe.api_key = ""


class PaymentServiceStripe(Component):

    _name = "payment.service.stripe"
    _inherit = "base.shopinvader.service"
    _usage = "payment_stripe"
    _description = ""

    def _allowed_payment_target(self):
        """
        Restrict service calls
        :return: list
        """
        return ["current_cart"]

    def _validator_confirm_payment(self):
        """
        Validator of confirm_payment service
        target: see _allowed_payment_target()
        payment_mode: The payment mode used to pay
        stripe_payment_intent_id: The previously created intent
        stripe_payment_method_id: The Stripe card created on client side
        :return: dict
        """
        return {
            "target": {
                "type": "string",
                "required": True,
                "allowed": self._allowed_payment_target(),
            },
            "payment_mode": {"type": "string"},
            "stripe_payment_intent_id": {"type": "string"},
            "stripe_payment_method_id": {"type": "string"},
        }

    def _validator_return_confirm_payment(self):
        return {
            "requires_action": {"type": "boolean"},
            "payment_intent_client_secret": {"type": "string"},
            "success": {"type": "boolean"},
            "error": {"type": "string"},
        }

    def _find_target(self):
        """
        Find the target object from a payment request dict
        supported targets: current_cart
        the returned object implements shopinvader.payable
        :return: recordset
        """
        cart_component = self.component(usage="cart")
        cart = cart_component._get()
        return cart

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

    def _get_stripe_private_key(self, tx_data=False, tx=False):
        """
        Return stripe private key depending on tx dict (before creation) or
        with payment.transaction recordset
        :param tx_data: dict
        :param tx: account.payment.mode
        :return: string
        """
        acquirer = self.env["payment.acquirer"]
        if tx:
            acquirer = tx.acquirer_id
        if tx_data and "payment_mode_id" in tx_data:
            acquirer = acquirer.browse(tx_data.get("acquirer_id"))
        return acquirer.filtered(
            lambda a: a.provider == "stripe"
        ).stripe_secret_key

    def confirm_payment(
        self,
        target,
        payment_mode=False,
        stripe_payment_method_id=False,
        stripe_payment_intent_id=False,
    ):
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
        :param payment_mode: string (The Odoo payment mode)
        :param stripe_payment_method_id:
        :param stripe_payment_intent_id:
        :return:
        """
        transaction_obj = self.env["payment.transaction"]
        target = self._find_target()
        intent = False
        error_message = ""
        tx_data = {}
        try:
            if stripe_payment_method_id:
                tx_data = target._prepare_payment_transaction_data(
                    payment_mode
                )
                with StripeKeyManager(
                    stripe, self._get_stripe_private_key(tx_data=tx_data)
                ):
                    intent = self._prepare_stripe_intent(
                        tx_data, stripe_payment_method_id
                    )
                if intent:
                    self._update_transaction_with_stripe(intent, tx_data)
                    tx = transaction_obj.create(tx_data)
                    target._attach_transaction(tx)
            elif stripe_payment_intent_id:
                tx = self._get_stripe_transaction_from_intent(
                    stripe_payment_intent_id
                )
                with StripeKeyManager(
                    stripe, self._get_stripe_private_key(tx=tx)
                ):
                    intent = self._confirm_stripe_intent(
                        stripe_payment_intent_id
                    )
                self._update_transaction_with_stripe(intent, tx_data)
                tx._set_transaction_done()
                tx.write(tx_data)

            # Update Transaction and cart with intent state
            if tx and tx.state == "done":
                cart_component = self.component(usage="cart")
                cart_component._action_after_payment(target)
        except (stripe.error.CardError, Exception) as e:
            error_message = "Transaction Error : {}".format(e)

        finally:
            if error_message:
                if tx:
                    # Odoo does not like to change
                    # not draft transaction to error
                    tx.write({"state": "draft"})
                    tx._set_transaction_error(error_message)

            return self._generate_stripe_response(intent, error_message)

    def _prepare_stripe_intent(self, tx_data, stripe_payment_method_id):
        """
        Prepare a StripeIntent with payment.transaction data
        :param tx_data:
        :param stripe_payment_method_id:
        :return: StripeIntent
        """
        currency_obj = self.env["res.currency"]
        currency = currency_obj.browse(tx_data.get("currency_id"))
        intent = stripe.PaymentIntent.create(
            payment_method=stripe_payment_method_id,
            amount=self._get_formatted_amount(currency, tx_data.get("amount")),
            currency=currency.name,
            confirmation_method="manual",
            confirm=True,
        )
        return intent

    def _update_transaction_with_stripe(self, intent, tx_data):
        """
        Update the payment.transaction dict with some Stripe references
        :param intent:
        :param tx_data:
        :return:
        """
        tx_data.update(
            {
                "acquirer_reference": intent.id,
                "state": STRIPE_TRANSACTION_STATUSES[intent.status],
            }
        )

    def _confirm_stripe_intent(self, stripe_payment_intent_id):
        """
        Confirm the Stripe Intent and return it
        :param stripe_payment_intent_id:
        :return: StripeIntent
        """
        return stripe.PaymentIntent.confirm(stripe_payment_intent_id)

    def _generate_stripe_response(self, intent=False, error_message=""):
        """
        This is the message returned to client
        :param intent: StripeIntent
        :param error_message: string
        :return: dict
        """
        if error_message:
            return {"error": error_message}
        if (
            intent
            and intent.status == "requires_action"
            and intent.next_action.type == "use_stripe_sdk"
        ):
            # Tell the client to handle the action
            return {
                "requires_action": True,
                "payment_intent_client_secret": intent.client_secret,
            }
        elif intent and intent.status == "succeeded":
            # The payment didn’t need any additional actions and completed!
            # Handle post-payment fulfillment
            return {"success": True}
        else:
            # Invalid status
            return {"error": "Invalid PaymentIntent status"}
