# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.addons.component.core import Component
from odoo.exceptions import UserError


class InvaderPaymentService(Component):

    _name = "invader.payment.service"
    _usage = "invader.payment"

    def _invader_find_payable_from_target(self, target, **params):
        """
        Find an invader.payable from a target parameter (e.g. current cart).

        target and params comply with the schema returned by
        ``_invader_get_target_validator``.
        """
        raise NotImplementedError()

    def _invader_find_payable_from_transaction(self, transaction):
        """
        Find the invader.payble linked to a payment.transaction.

        This method is used to inform the payable when a transaction was
        accepted, in situations where we are informed of payment success
        through a webhook call from the payment acquirer.

        TODO: in a future refactoring, we should eliminate
        ``_invader_payment_accepted`` which is possible if the payable
        "listens" for state change events on its associated
        ``payment.transaction``.
        In that case ``_invader_find_payable_from_transaction`` can be
        removed too.
        """
        raise NotImplementedError()

    def _invader_get_target_validator(self):
        """
        Return a cerberus validator schema fragment that specifies the
        target being paid. Implementations must extend it by populating
        the "allowed" field (eg with strings such as 'current_cart') and
        possibly adding other fields.
        """
        return {"target": {"type": "string", "required": True, "allowed": []}}

    def _invader_get_payment_success_reponse_data(
        self, payable, target, **params
    ):
        """
        This is mostly used by ShopInvader to manipulate session and
        store_cache after payment success.

        TODO: this method will go away when a better mechanism for Shopinvader
        session management is in place.
        """
        return {}

    def _check_acquirer(self, payment_mode, provider):
        """Check that the payment mode have the correct provider
        If the provider is not the same, raise an error
        """
        acquirer = payment_mode.payment_acquirer_id.sudo()
        if acquirer.provider != provider:
            raise UserError(
                _(
                    "Payment mode acquirer mismatch should be "
                    "'{}' instead of '{}'."
                ).format(provider, acquirer.provider)
            )
