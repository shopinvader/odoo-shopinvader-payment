# -*- coding: utf-8 -*-
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

    def _invader_get_target_validator(self):
        """
        Return a cerberus validator schema fragment that specifies the
        target being paid. Implementations must extend it by populating
        the "allowed" field (eg with strings such as 'current_cart') and
        possibly adding other fields.
        """
        return {"target": {"type": "string", "required": True, "allowed": []}}

    def _check_provider(self, payment_mode, provider):
        """Check that the payment mode has the correct provider
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
