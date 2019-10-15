# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.addons.payment_stripe.models.payment import INT_CURRENCIES
from odoo.tools.float_utils import float_round

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
    "RedirectShopper": "pending",
}
APP_NAME = "INVADER"


class PaymentServiceAdyen(AbstractComponent):

    _name = "payment.service.adyen"
    _inherit = "base.rest.service"
    _usage = "payment_adyen"
    _description = "REST Services for Adyen payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _get_platform(self, transaction):
        """
        Return 'test' or 'live' depending on acquirer value
        :param transaction:
        :return:
        """
        environment = transaction.acquirer_id.environment
        return environment if environment == "test" else "live"

    def _validator_paymentMethods(self):
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "merchantAccount": {"type": "string", "required": True},
                "payment_mode_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "countryCode": {"type": "string"},
                "amount": {
                    "type": "dict",
                    "schema": {
                        "value": {"coerce": int, "required": True},
                        "currency": {"type": "string"},
                    },
                },
                "channel": {"type": "string"},
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
        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)
        self.payment_service._check_provider(payment_mode, "adyen")

        # Get available payment methods for the transacation details
        # NOTE: Not created at the moment
        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(payment_mode)
        )
        response = self._prepare_adyen_payment_methods_request(transaction)
        return self._generate_adyen_response(
            response, payable, target, transaction, **params
        )

    def _prepare_adyen_payment_methods_request(self, transaction):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-1-get-available-payment-methods

        Prepare and call Adyen to retrieve available payment methods
        :param transaction:
        :return:
        """
        adyen = Adyen.Adyen(
            app_name=APP_NAME, platform=self._get_platform(transaction)
        )
        adyen.client.xapikey = self._get_adyen_api_key(transaction)
        currency = transaction.currency_id
        amount = transaction.amount
        request = {
            "merchantAccount": self._get_adyen_merchant_account(transaction),
            "countryCode": transaction.partner_id.country_id.code,
            "amount": {
                "value": self._get_formatted_amount(currency, amount),
                "currency": currency.symbol,
            },
            "channel": "Web",
        }
        response = adyen.checkout.payment_methods(request)
        return response

    def _validator_payments(self):
        """
        Validator of payments service
        target: see _allowed_payment_target()
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
                "adyen_payment_method_id": {"type": "string"},
                "payment_method": {"type": "dict"},
                "return_url": {"type": "string"},
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

    def payments(self, target, **params):
        payment_mode_id = params.get("payment_mode_id")
        transaction_id = params.get("transaction_id")
        payment_method = params.get("payment_method")
        return_url = params.get("return_url")
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        # Adyen part
        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)
        self.payment_service._check_provider(payment_mode, "adyen")

        transaction = transaction_obj.browse(transaction_id)
        transaction.return_url = return_url
        response = self._prepare_adyen_payments_request(
            transaction, payment_method
        )
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
        Prepare and call Adyen payments request
        :param transaction:
        :param payment_method:
        :return:
        """
        adyen = Adyen.Adyen(
            app_name=APP_NAME, platform=self._get_platform(transaction)
        )
        adyen.client.xapikey = self._get_adyen_api_key(transaction)
        currency = transaction.currency_id
        amount = transaction.amount
        request = {
            "merchantAccount": self._get_adyen_merchant_account(transaction),
            "countryCode": transaction.partner_country_id.code,
            "reference": transaction.reference,
            "amount": {
                "value": self._get_formatted_amount(currency, amount),
                "currency": currency.name,
            },
            "channel": "Web",
            "paymentMethod": payment_method,
            "returnUrl": transaction.return_url,
            "additionalData": {"executeThreeD": True},
        }
        response = adyen.checkout.payments(request)
        # Update transaction with required details in further Adyen calls
        vals = {
            "adyen_payment_data": response.message.get("paymentData"),
            "acquirer_reference": response.message.get("pspReference"),
        }
        transaction.update(vals)
        return response

    def _prepare_payment_details(self, transaction_id, **params):
        transaction = self.env["payment.transaction"].browse(
            int(transaction_id)
        )
        adyen = Adyen.Adyen(
            app_name=APP_NAME, platform=self._get_platform(transaction)
        )
        adyen.client.xapikey = self._get_adyen_api_key(transaction)
        adyen.client.xapikey = self._get_adyen_api_key(transaction)
        params.pop("success_redirect")
        params.pop("target")
        params.pop("cancel_redirect")
        request = {
            "paymentData": transaction.adyen_payment_data,
            "details": params,
        }
        response = adyen.checkout.payments_details(request)
        return response

    def _validator_payments_details(self):
        """
        Validator of payments service
        target: see _allowed_payment_target()
        payment_mode_id: The payment mode used to pay
        stripe_payment_intent_id: The previously created intent
        stripe_payment_method_id: The Stripe card created on client side
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update({"data": {"type": "dict", "required": True}})
        return res

    def _validator_return_payments_details(self):
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
        response = self._prepare_payment_details(**params)
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
        response = self._prepare_payment_details(**params)
        result_code = response.message.get("resultCode")
        return_url = params.get("success_redirect")
        if result_code == "Authorised":
            transaction._set_transaction_done()
        elif result_code in ("Cancelled", "Refused"):
            return_url = params.get("cancel_redirect")
            transaction.write(
                {"state": ADYEN_TRANSACTION_STATUSES[result_code]}
            )
        else:
            transaction.write(
                {"state": ADYEN_TRANSACTION_STATUSES[result_code]}
            )
        res = {}
        res["redirect_to"] = return_url
        return res

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
        Return adyen merchant account depending on payment.transaction recordset
        :param transaction: payment.transaction
        :return: string
        """

        acquirer = transaction.acquirer_id
        return acquirer.filtered(
            lambda a: a.provider == "adyen"
        ).adyen_merchant_account

    def _generate_adyen_response(
        self, response, payable, target, transaction=False, **params
    ):
        """
        This is the message returned to client
        :param response: The response generated by Adyen call
        :param payable: invader.payable record
        :return: dict
        """
        if response:
            message = response.message
            if transaction:
                message.update({"transaction_id": transaction.id})
            return message
        return {"error": _("Payment Error")}
