# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import stripe
from odoo import _, api, models

_logger = logging.getLogger(__name__)

# map Stripe transaction statuses to Odoo payment.transaction statuses
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


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    @api.multi
    def _charge_get_formatted_amount(self):
        """
        Transform the amount to correspond to the acquirer
        :return: type needed bu the acquirer provider (float/int)
        """
        self.ensure_one()
        return self.amount

    @api.multi
    def charge_source(self):
        """
        This is the rest service exposed to locomotive and called on
        payment confirmation.
        Called to charge the source (created in the front end)
        :param source: string (id of the stripe source)
        :return:
        """
        charge = False
        try:
            charge = stripe.Charge.create(
                amount=self._charge_get_formatted_amount(),
                currency=self.currency_id.name,
                source=self.acquirer_reference,
                api_key=self.acquirer_id.stripe_secret_key,
            )
            # update the acquirer with the charge id instead of the source id,
            # since later the charge (which really removed the money)
            # which will be used
            self.write({"acquirer_reference": charge.id})
            if charge.status == "succeeded":
                # Handle post-payment fulfillment
                self._set_transaction_done()
            else:
                self.write(
                    {"state": STRIPE_TRANSACTION_STATUSES[charge.status]}
                )
        except Exception as e:
            _logger.error("Error charging stripe payment", exc_info=True)
            # Odoo does not like to change not draft transaction to error
            self.write({"state": "draft"})
            self._set_transaction_error(_("Exception: {}").format(e))
            raise
        return charge
