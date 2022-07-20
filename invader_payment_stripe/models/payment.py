# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentAcquirerStripe(models.Model):
    _inherit = "payment.acquirer"

    def _handle_stripe_webhook(self, data):
        wh_type = data.get("type")
        if wh_type == "payment_intent.succeeded":
            return self._handle_stripe_intent_succeeded_webhook(data)
        else:
            return super()._handle_stripe_webhook(data)

    def _handle_stripe_intent_succeeded_webhook(self, data):
        payment_intent = data.get("data", {}).get(
            "object"
        )  # contains a stripe.PaymentIntent
        if not payment_intent:
            raise ValidationError(
                _("Stripe Webhook data does not conform to the expected API.")
            )
        acquirer = self.env.ref("payment.payment_acquirer_stripe")
        acquirer._verify_stripe_signature()
        reference = payment_intent["metadata"].get("reference")
        transaction = self.env["payment.transaction"].search(
            [
                ("reference", "=", reference),
                ("acquirer_reference", "=", payment_intent["id"]),
            ],
            limit=1,
        )
        if not transaction:
            raise ValidationError(
                _(
                    "payment_intent.succeeded event received \
                            for an unknown transaction: {}, {}"
                ).format(reference, payment_intent["id"])
            )
        _logger.info(_("Payment for {} succeeded").format(transaction.reference))
        if "amount" in payment_intent:
            transaction.amount = payment_intent["amount"] / 100  # Amount is in cents
        transaction._set_transaction_done()
        return True
