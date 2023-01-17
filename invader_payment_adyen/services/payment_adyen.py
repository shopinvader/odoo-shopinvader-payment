# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import (
    skip_secure_response,
    to_bool,
    to_int,
)
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    import Adyen
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
APP_NAME = "INVADER"

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

    _name = "payment.service.adyen"
    _inherit = "base.rest.service"
    _usage = "payment_adyen"
    _description = "REST Services for Adyen payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _get_adyen_service(self, transaction):
        """
        Return an intialized library
        :param transaction:
        :return:
        """
        adyen = Adyen.Adyen(
            platform=self._get_platform(transaction),
            live_endpoint_prefix=self._get_live_prefix(transaction),
            xapikey=self._get_adyen_api_key(transaction),
        )
        return adyen

    def _get_platform(self, transaction):
        """
        Return 'test' or 'live' depending on acquirer value
        :param transaction:
        :return: str
        """
        return transaction._get_platform()

    def _get_live_prefix(self, transaction):
        state = transaction.acquirer_id.state
        prefix = transaction.acquirer_id.adyen_live_endpoint_prefix
        return str(prefix) if state == "enabled" else ""

    def _validator_paymentMethods(self):
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "payment_mode_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                }
            }
        )
        return res

    def _validator_return_paymentMethods(self):
        return Validator(
            {
                "paymentMethods": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                        },
                    },
                },
                "transaction_id": {"type": "integer"},
            },
            allow_unknown=True,
        )

    def paymentMethods(self, target, **params):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-1-get-available-payment-methods

        This is the service to provide Payment Methods depending on transaction
        details and on partner country.

        :return:
        """
        payment_mode_id = params.get("payment_mode_id")
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        # Adyen part
        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        self.payment_service._check_provider(acquirer, "adyen")

        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(acquirer)
        )
        request = self._prepare_adyen_payment_methods_request(transaction)
        adyen = self._get_adyen_service(transaction)
        response = adyen.checkout.payment_methods(request)
        return self._generate_adyen_response(
            response, payable, target, transaction, **params
        )

    def _prepare_adyen_payment_methods_request(self, transaction):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-1-get-available-payment-methods

        Prepare retrieval of available payment methods
        :param transaction:
        :return:
        """

        currency = transaction.currency_id
        amount = transaction.amount
        request = {
            "merchantAccount": self._get_adyen_merchant_account(transaction),
            "countryCode": transaction.partner_id.country_id.code,
            "amount": {
                "value": self._get_formatted_amount(transaction, amount),
                "currency": currency.name,
            },
            "channel": "Web",
        }
        return request

    def _validator_payments(self):
        """
        Validator of payments service
        target: see _invader_get_target_validator()
        payment_mode_id: The payment mode used to pay
        transaction_id: As the request to Adyen so not create some kind of
            transaction 'token', we must pass the transaction_id to the flow
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
                "transaction_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "payment_method": {"type": "dict", "required": True},
                "return_url": {"type": "string", "required": True},
            }
        )
        return res

    def _validator_return_payments(self):
        return Validator(
            {
                "redirect": {
                    "type": "dict",
                    "schema": {
                        "data": {"type": "dict"},
                        "url": {"type": "string"},
                        "method": {"type": "string"},
                    },
                },
                "resultCode": {"type": "string"},
                "pspReference": {"type": "string"},
                "details": {"type": "list"},
                "action": {"type": "dict"},
            },
            allow_unknown=True,
        )

    def payments(
        self,
        target,
        transaction_id,
        payment_mode_id,
        payment_method,
        return_url,
        **params
    ):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment


        :param target: the payable (e.g.: "current_cart")
        :param transaction_id: the previously created transaction
        :param payment_mode_id: the payment mode
        :param payment_method: the Adyen payment method (bcmc, scheme, ...)
        :param return_url: the url to return to (in case of redirect)
        :param params: other parameters
        :return:
        """
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        self.payment_service._check_provider(acquirer, "adyen")

        transaction = transaction_obj.browse(transaction_id)
        transaction.return_url = return_url
        request = self._prepare_adyen_payments_request(
            transaction, payment_method
        )
        adyen = self._get_adyen_service(transaction)
        response = adyen.checkout.payments(request)
        self._update_transaction_with_response(transaction, response)
        result_code = response.message.get("resultCode")
        if result_code == "Authorised":
            transaction._set_transaction_done()
        else:
            transaction.write(
                {"state": ADYEN_TRANSACTION_STATUSES[result_code]}
            )

        return self._generate_adyen_response(
            response, payable, target, transaction, **params
        )

    def _prepare_adyen_payments_request(self, transaction, payment_method):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment
        Prepare payments request
        :param transaction:
        :param payment_method:
        :return:
        """
        currency = transaction.currency_id
        amount = transaction.amount
        request = {
            "merchantAccount": self._get_adyen_merchant_account(transaction),
            "countryCode": transaction.partner_country_id.code,
            "reference": transaction.reference,
            "amount": {
                "value": self._get_formatted_amount(transaction, amount),
                "currency": currency.name,
            },
            "channel": "Web",
            "paymentMethod": payment_method,
            "returnUrl": transaction.return_url,
            "additionalData": {"executeThreeD": True},
        }

        return request

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
            "paymentData": transaction.adyen_payment_data,
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

        Intended to manage onAddtionalDetails event from drop-in component
        :param params:
        :return:
        """
        transaction_id = params.get("transaction_id")
        transaction = self.env["payment.transaction"].browse(transaction_id)
        adyen = self._get_adyen_service(transaction)
        request = self._prepare_payment_details(transaction, **params)
        response = adyen.checkout.payments_details(request)

        return response

    def _validator_paymentResult(self):
        schema = {
            "transaction_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "success_redirect": {"type": "string"},
            "cancel_redirect": {"type": "string"},
        }
        return Validator(schema, allow_unknown=True)

    def _validator_return_paymentResult(self):
        schema = {"redirect_to": {"type": "string"}}
        return Validator(schema, allow_unknown=True)

    @restapi.method(
        [(["/paymentResult"], ["GET", "POST"])],
        input_param=restapi.CerberusValidator("_validator_paymentResult"),
        output_param=restapi.CerberusValidator(
            "_validator_return_paymentResult"
        ),
    )
    def paymentResult(self, **params):
        """
        This is intended to manage callbacks after a merchant redirection
        (3DS, challenge, ...)
        :param params:
        :return:
        """
        transaction = self.env["payment.transaction"].browse(
            params.get("transaction_id")
        )
        # Response will be an AdyenResult object
        adyen = self._get_adyen_service(transaction)
        request = self._prepare_payment_details(transaction, **params)
        response = adyen.checkout.payments_details(request)
        self._update_transaction_with_response(transaction, response)
        result_code = response.message.get("resultCode")
        return_url = params.get("success_redirect")
        notify = False
        if result_code == "Authorised":
            if transaction.state == "draft":
                transaction._set_transaction_done()
            else:
                notify = True
        elif result_code in ("Cancelled", "Refused"):
            return_url = params.get("cancel_redirect")
            transaction.write(
                {"state": ADYEN_TRANSACTION_STATUSES[result_code]}
            )
        else:
            transaction.write(
                {"state": ADYEN_TRANSACTION_STATUSES[result_code]}
            )

        if notify:
            # Payment state has been changed through another process
            # (e.g. webhook). So, do the stuff for shopinvader_session
            transaction._notify_state_changed_event()
        res = {}
        res["redirect_to"] = return_url
        return res

    def _get_formatted_amount(self, transaction, amount):
        """
        The expected amount format by Adyen
        :param amount: float
        :return: int
        """
        return self.env["invader.payable"]._get_formatted_amount(
            transaction, amount
        )

    def _get_adyen_api_key(self, transaction):
        """
        Return adyen api key depending on payment.transaction recordset
        :param transaction: payment.transaction
        :return: string
        """

        acquirer = transaction.acquirer_id
        return acquirer.filtered(lambda a: a.provider == "adyen").adyen_api_key

    def _get_adyen_merchant_account(self, transaction):
        """
        Return adyen merchant account depending on
        payment.transaction recordset
        :param transaction: payment.transaction
        :return: string
        """

        acquirer = transaction.acquirer_id
        return acquirer.filtered(
            lambda a: a.provider == "adyen"
        ).adyen_merchant_account

    def _update_additional_details(self, response):
        """
        Hook to be able to enrich transaction with response
        additionalData
        Payment result can contains payment method brand
        """
        res = {}
        if response.message.get("action", {}).get("paymentMethodType"):
            payment_method = response.message.get("action", {}).get(
                "paymentMethodType"
            )
            res.update({"adyen_payment_method": payment_method})
        if response.message.get("paymentMethod", {}).get("type"):
            payment_method = response.message.get("paymentMethod", {}).get(
                "type"
            )
            res.update({"adyen_payment_method": payment_method})
        if response.message.get("paymentMethod", {}).get("brand"):
            payment_method = response.message.get("paymentMethod", {}).get(
                "brand"
            )
            res.update({"adyen_payment_method": payment_method})
        return res

    def _update_transaction_with_response(self, transaction, response):
        """
        Update the transaction with Adyen response
        :param transaction: payment.transaction
        :param response: AdyenResult
        :return:
        """
        vals = {}
        vals.update(self._update_additional_details(response))
        payment_data = response.message.get("paymentData")
        if payment_data:
            vals.update({"adyen_payment_data": payment_data})
        psp_reference = response.message.get("pspReference") or getattr(
            response, "psp", ""
        )
        if psp_reference:
            vals.update({"acquirer_reference": psp_reference})
        result_code = response.message.get("resultCode")
        if result_code:
            # Log resultCode of Adyen in transaction
            message = transaction.state_message
            stamp = str(fields.Datetime.now())
            adyen_message = "\n" + stamp + ": " + str(response.message)
            if message:
                message += adyen_message
            else:
                message = adyen_message
            vals.update({"state_message": message})
        transaction.update(vals)

    def _generate_adyen_response(
        self, response, payable, target, transaction=False, **params
    ):
        """
        This is the message returned to client
        :param response: The response generated by Adyen call (AdyenResult)
        :param payable: invader.payable record
        :return: dict
        """

        message = response.message
        if transaction:
            message.update({"transaction_id": transaction.id})
        return message

    def _validator_webhook(self):
        schema = {
            "live": {"coerce": to_bool, "required": True},
            "notificationItems": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "NotificationRequestItem": {
                            "type": "dict",
                            "schema": {"additionalData": {"type": "dict"}},
                        }
                    },
                },
            },
        }
        return Validator(schema, allow_unknown=True)

    def _validator_return_webhook(self):
        """
        Returns nothing
        :return:
        """
        schema = {}
        return Validator(schema, allow_unknown=True)

    @skip_secure_response
    def webhook(self, **params):
        """
        Implement the webhook notification.
        See: https://docs.adyen.com/development-resources/notifications
        :param params:
        :return:
        """
        payment_acquirer_obj = self.env["payment.acquirer"]
        for element in params.get("notificationItems"):
            notification_item = element.get("NotificationRequestItem")
            with self.env.cr.savepoint():
                # Continue to handle items even if error
                payment_acquirer_obj._handle_adyen_notification_item(
                    notification_item
                )
        return "[accepted]"
