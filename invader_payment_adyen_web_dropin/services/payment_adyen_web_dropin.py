# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# isort: skip_file
# Need to skip this file because conflict with black
import logging

from odoo import _

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import (
    skip_secure_response,
    to_int,
)
from odoo.addons.component.core import AbstractComponent
from odoo.addons.invader_payment.models.payment_acquirer import (
    PAYMENT_BASE_URL_KEY,
)

from ..models.payment_acquirer import ADYEN_PROVIDER
from .exceptions import AdyenInvalidData

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError as err:
    _logger.debug(err)


class PaymentServiceAdyenWebDropin(AbstractComponent):

    _name = "payment.service.adyen_web_dropin"
    _inherit = "payment.service.adyen.abstract"
    _usage = "payment_adyen_dropin"
    _description = "REST Services for Adyen web-dropin payments"

    def _validator_payments(self):
        """
        Validator of payments service
        target: see _invader_get_target_validator()
        payment_mode_id: The payment mode used to pay
        transaction_id: As the request to Adyen so not create some kind of
            transaction 'token', we must pass the transaction_id to the flow
        :return: dict
        """
        schema = self.payment_service._invader_get_target_validator()
        schema.update(
            {
                "acquirer_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "return_url": {"type": "string", "required": False},
            }
        )
        return schema

    def _validator_return_payments(self):
        return Validator({}, allow_unknown=True)

    def payments(self, target, acquirer_id, return_url=False, **params):
        """
        Trigger the Adyen session to execute the payment
        :return: json
        """
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )
        if not payable:
            raise AdyenInvalidData(_("No payable found"))
        # Adyen part
        acquirer = (
            self.env["payment.acquirer"]
            .with_context(**{PAYMENT_BASE_URL_KEY: return_url})
            .search(
                [("id", "=", acquirer_id), ("provider", "=", ADYEN_PROVIDER)],
                limit=1,
            )
        )
        transaction = (
            self.env["payment.transaction"]
            .with_context(**{PAYMENT_BASE_URL_KEY: return_url})
            .create(
                payable._invader_prepare_payment_transaction_data(acquirer)
            )
        )
        response = transaction.trigger_transaction()
        return response

    def _validator_webhook(self):
        schema = {
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
        return Validator({}, allow_unknown=True)

    @skip_secure_response
    @restapi.method(
        [(["/webhook"], ["GET", "POST"])],
        input_param=restapi.CerberusValidator("_validator_webhook"),
        output_param=restapi.CerberusValidator("_validator_return_webhook"),
    )
    def webhook(self, **params):
        """
        Implement the webhook notification.
        See: https://docs.adyen.com/development-resources/notifications
        Example of webhook for a successful payment:
        {
          "live": "false",
          "notificationItems":[
            {
              "NotificationRequestItem":{
                "eventCode":"AUTHORISATION",
                "merchantAccountCode":"YOUR_MERCHANT_ACCOUNT",
                "reason":"033899:1111:03/2030",
                "amount":{
                  "currency":"EUR",
                  "value":2500
                },
                "operations":["CANCEL","CAPTURE","REFUND"],
                "success":"true",
                "paymentMethod":"mc",
                "additionalData":{
                  "expiryDate":"03/2030",
                  "authCode":"033899",
                  "cardBin":"411111",
                  "cardSummary":"1111",
                  "checkoutSessionId":"CSF46729982237A879"
                },
                "merchantReference":"YOUR_REFERENCE",
                "pspReference":"NC6HT9CRT65ZGN82",
                "eventDate":"2021-09-13T14:10:22+02:00"
              }
            }
          ]
        }

        And an unsuccessful payment:
        {
          "live": "false",
          "notificationItems":[
            {
              "NotificationRequestItem":{
                "eventCode":"AUTHORISATION",
                "merchantAccountCode":"YOUR_MERCHANT_ACCOUNT",
                "reason":"validation 101 Invalid card number",
                "amount":{
                  "currency":"EUR",
                  "value":2500
                },
                "success":"false",
                "paymentMethod":"unknowncard",
                "additionalData":{
                  "expiryDate":"03/2030",
                  "cardBin":"411111",
                  "cardSummary":"1112",
                  "checkoutSessionId":"861631540104159H"
                },
                "merchantReference":"YOUR_REFERENCE",
                "pspReference":"KHQC5N7G84BLNK43",
                "eventDate":"2021-09-13T14:14:05+02:00"
              }
            }
          ]
        }
        :param transaction_id: int (optional)
        :param params:
        :return: str
        """
        # In case of exception, Adyen recommends to not return anything
        try:
            return self.env["payment.transaction"].manage_adyen_dropin_webhook(
                params, queue_job=True
            )
        except Exception:
            return ""

    def _validator_transaction_details(self):
        schema = {
            "transaction_id": {
                "required": True,
                "type": "string",
            },
        }
        return Validator(schema, allow_unknown=False)

    def _validator_return_transaction_details(self):
        """
        Returns nothing
        :return:
        """
        schema = {
            "reference": {"type": "string", "required": True},
            "amount": {"type": "float", "required": True},
            "currency": {"type": "string", "required": True},
            "acquirer_reference": {"type": "string", "required": True},
            "state_technical": {"type": "string", "required": True},
            "adyen_payment_method": {"type": "string", "required": True},
            "state": {"type": "string", "required": True},
        }
        return Validator(schema, allow_unknown=False)

    @skip_secure_response
    @restapi.method(
        [(["/transaction_details"], ["GET"])],
        input_param=restapi.CerberusValidator(
            "_validator_transaction_details"
        ),
        output_param=restapi.CerberusValidator(
            "_validator_return_transaction_details"
        ),
    )
    def transaction_details(self, transaction_id):
        # The transaction_id is the acquirer_reference
        domain = [
            ("acquirer_reference", "=", transaction_id),
            ("acquirer_id.provider", "=", ADYEN_PROVIDER),
        ]
        transaction = self.env["payment.transaction"].search(domain, limit=1)
        return {
            "reference": transaction.reference,
            "amount": transaction.amount,
            "currency": transaction.currency_id.symbol,
            "acquirer_reference": transaction.acquirer_reference,
            "state_technical": transaction.state,
            "adyen_payment_method": transaction.adyen_payment_method or "",
            "state": transaction._fields.get("state").convert_to_export(
                transaction["state"], transaction
            ),
        }
