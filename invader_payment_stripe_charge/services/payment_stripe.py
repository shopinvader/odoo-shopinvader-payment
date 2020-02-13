# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentServiceStripe(AbstractComponent):

    _inherit = "payment.service.stripe"

    def _get_chargeable_provider(self):
        """
        Overwrite to add providers which use the charge api
        :return: list of str
        """
        return []

    def _validator_source_created(self):
        """
        Validator of source_created service
        payment_mode_id: The payment mode used to pay
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
                "source": {"type": "string"},
            }
        )
        return res

    def _validator_return_source_created(self):
        return {"success": {"type": "boolean"}, "error": {"type": "string"}}

    def source_created(self, target, **params):
        """
        This is the rest service exposed to locomotive and called on
        payment creation.
        Called to create the transaction in pending
        (source created in the front end)
        :param target: string (authorized value is checked by service)
        :param payment_mode_id: string (The Odoo payment mode id)
        :param source: string (id of the stripe source)
        :return:
        """
        payment_mode_id = params.get("payment_mode_id")
        source = params.get("source")
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        # Stripe part
        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        try:
            provider_found = False
            providers = self._get_chargeable_provider()
            for provider in providers:
                try:
                    self.payment_service._check_provider(acquirer, provider)
                    provider_found = True
                    break
                except UserError:
                    # pass silently, if there is really a error to raise,
                    # will be raise later
                    pass
            if not provider_found:
                raise UserError(
                    _(
                        "Payment mode acquirer mismatch should be in '{}' "
                        "instead of '{}'."
                    ).format(providers, acquirer.provider)
                )
            transaction_vals = payable._invader_prepare_payment_transaction_data(
                acquirer
            )
            transaction_vals["acquirer_reference"] = source
            transaction_obj.create(transaction_vals)
        except Exception:
            _logger.error(
                "Error creating transaction for source", exc_info=True
            )
            return {"error": _("Payment Error")}
        return {"success": True}

    def _validator_charge_source(self):
        return {"source": {"type": "string"}}

    def _validator_return_charge_source(self):
        return {"success": {"type": "boolean"}, "error": {"type": "string"}}

    def charge_source(self, source):
        """
        This is the rest service exposed to locomotive and called on
        payment confirmation.
        Called to charge the source (created in the front end)
        :param source: string (id of the stripe source)
        :return:
        """
        transaction_obj = self.env["payment.transaction"]
        try:
            transaction = transaction_obj.search(
                [("acquirer_reference", "=", source)]
            )
            charge = transaction.charge_source()
            return self._charge_generate_stripe_response(charge)
        except Exception:
            return self._charge_generate_stripe_error_response()

    def _charge_generate_stripe_response(self, charge):
        """
        This is the message returned to client
        :return: dict
        """
        if charge:
            if charge.status == "succeeded":
                # The payment didn’t need any additional actions and completed!
                return {"success": True}
            if charge.status == "canceled":
                return {"error": _("Payment canceled.")}
        return {"error": _("Payment Error")}

    def _charge_generate_stripe_error_response(self):
        return self._charge_generate_stripe_response(None)
