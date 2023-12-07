# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError as err:
    _logger.debug(err)

# map Adyen transaction statuses to Odoo payment.transaction statuses
ADYEN_TRANSACTION_STATUSES = {
    "Authorised": "done",
    "Refused": "error",
    "Cancelled": "cancel",
    "Received": "pending",
    "RedirectShopper": "draft",
}

payment_completion_details = [
    "MD",
    "PaReq",
    "PaRes",
    "billingToken",
    "cupsecureplus.smscode",
    "facilitatorAccessToken",
    "oneTimePasscode",
    "orderID",
    "payerID",
    "payload",
    "paymentID",
    "paymentStatus",
    "redirectResult",
    "returnUrlQueryString",
    "threeds2.challengeResult",
    "threeds2.fingerprint",
]


def filter_completion_details(details):
    """
    Filter authorized details in order to pass just those ones to the API

    :param details: The details values as a dict
    :type details: dict
    """
    if not details:
        return
    unknown_params = []
    new_details = {}
    for key, value in details.items():
        if key not in payment_completion_details:
            unknown_params.append(key)
        else:
            new_details[key] = value
    if unknown_params:
        # Log unknown keys
        message = (
            "PaymentCompletionDetails contains unknown params: %s"
            % ",".join([str(param) for param in unknown_params])
        )
        _logger.info(message)
    return new_details


class PaymentServiceAdyen(AbstractComponent):
    _name = "payment.service.adyen.abstract"
    _inherit = "base.rest.service"
    _usage = "payment_adyen"
    _description = "REST Services for Adyen payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _get_service(self, transaction):
        """
        Return an intialized library
        :param transaction:
        :return:
        """
        return transaction._get_service()

    def _prepare_payment_details(self, transaction, **params):
        """
        Remove specific entries from params and keep received by Adyen ones
        Pass saved paymentData on transaction level to request
        :param transaction:
        :param params:
        :return:
        """
        params = filter_completion_details(params)
        request = {
            "paymentData": transaction.adyen_payment_data or "",
            "details": params,
        }
        return request

    def _validator_payment_details(self):
        """
        Validator of payments service
        target: see _allowed_payment_target()
        payment_mode_id: The payment mode used to pay
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "data": {"type": "dict", "required": True},
                "transaction_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
            }
        )
        return res

    def _validator_return_payment_details(self):
        return Validator(
            {
                "resultCode": {"type": "string"},
                "pspReference": {"type": "string"},
                "action": {"type": "dict"},
            },
            allow_unknown=True,
        )

    def payment_details(self, **params):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-5-additional-payment-details
        https://docs.adyen.com/api-explorer/Checkout/70/post/payments/details
        Intended to manage onAddtionalDetails event from drop-in component
        :param params:
        :return:
        """
        transaction_id = params.get("transaction_id")
        transaction = (
            self.env["payment.transaction"]
            .browse(transaction_id)
            .filtered(lambda t: "adyen" in t.acquirer_id.provider)
        )
        adyen = self._get_service(transaction)
        request = self._prepare_payment_details(transaction, **params)
        response = adyen.checkout.payments_details(request)
        return response

    def _get_formatted_amount(self, transaction, amount):
        """
        The expected amount format by Adyen
        :param amount: float
        :return: int
        """
        return transaction._get_formatted_amount(force_amount=amount)

    def _update_additional_details(self, response):
        """
        Hook to be able to enrich transaction with response
        additionalData
        Deprecated. Should be filled on the transaction
        :param vals:
        :param response:
        :return:
        """
        _logger.warning(
            "DEPRECATED: You should use _update_additional_details() on the transaction"
        )
        return {}
