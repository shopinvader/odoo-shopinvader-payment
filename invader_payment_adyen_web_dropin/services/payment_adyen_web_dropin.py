# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# isort: skip_file
# Need to skip this file because conflict with black
import logging


from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import (
    skip_secure_response,
)
from odoo.addons.component.core import AbstractComponent
from ..models.payment_acquirer import ADYEN_PROVIDER


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

    def _get_adyen_provider(self):
        return ADYEN_PROVIDER

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
        [(["/webhook"], ["POST"])],
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
