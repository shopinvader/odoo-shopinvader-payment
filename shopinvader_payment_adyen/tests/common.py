# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import Adyen
from Adyen.util import generate_notification_sig


class ShopinvaderAdyenCommon(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shopinvader_payment = cls.env.ref(
            "shopinvader_payment_adyen.shopinvader_payment_adyen"
        )
        cls.acquirer = cls.shopinvader_payment.acquirer_id
        cls.acquirer.adyen_hmac_key = (
            "1994F46BDCF6E02FC68EE6252B84F31FCB76CC46771A95C335EBB0BE036A0DBF"
        )

        cls.data = {"target": "current_cart"}
        # https://docs.adyen.com/checkout/drop-in-web#-paymentmethods-response
        vals = {
            "paymentMethods": [
                {"name": "SEPA", "type": "sepadirectdebit"},
                {"name": "Credit Card", "type": "scheme"},
            ]
        }
        cls.payment_method_response = Adyen.client.AdyenResult(message=vals)
        vals = {
            "pspReference": "881572960484022G",
            "resultCode": "Received",
            "merchantReference": "YOUR_ORDER_NUMBER",
        }
        cls.payments_response = Adyen.client.AdyenResult(message=vals)
        vals = {
            "pspReference": "881572960484022G",
            "resultCode": "Authorised",
            "merchantReference": "YOUR_ORDER_NUMBER",
        }
        cls.payments_response_scheme = Adyen.client.AdyenResult(message=vals)

    @classmethod
    def _get_adyen_service(cls):
        adyen = Adyen.Adyen(
            platform="test", live_endpoint_prefix="prefix", xapikey="TEST"
        )
        return adyen

    @classmethod
    def _get_notification_item(cls, transaction, success=True):
        item = {
            "NotificationRequestItem": {
                "operations": ["CANCEL", "CAPTURE", "REFUND"],
                "additionalData": {
                    "authCode": "075362",
                    "cardHolderName": "Checkout Shopper PlaceHolder",
                    "cardSummary": "0000",
                    "expiryDate": "03/2030",
                },
                "eventCode": "AUTHORISATION",
                "merchantReference": transaction.reference,
                "merchantAccountCode": "Test",
                "pspReference": "psp_reference_1",
                "reason": "075362:0000:03/2030",
                "amount": {"currency": "EUR", "value": 299900},
                "success": "true" if success else "false",
                "paymentMethod": "visa",
                "eventDate": "2020-11-23T11:14:12+01:00",
            }
        }
        signature = cls._adyen_generate_notification_sig(
            item["NotificationRequestItem"],
            transaction.acquirer_id.adyen_hmac_key,
        )
        item["NotificationRequestItem"]["additionalData"][
            "hmacSignature"
        ] = str(signature.decode("utf-8"))
        return item

    @classmethod
    def _adyen_generate_notification_sig(cls, notification_request_item, hmac):
        return generate_notification_sig(
            notification_request_item,
            hmac,
        )

    def _regenerate_signature(self, request):
        for element in request.get("notificationItems"):
            notification_req_item = element.get("NotificationRequestItem")
            signature = self._adyen_generate_notification_sig(
                notification_req_item,
                self.transaction.acquirer_id.adyen_hmac_key,
            )
            notification_req_item["additionalData"]["hmacSignature"] = str(
                signature.decode("utf-8")
            )

    @classmethod
    def _get_notifications(cls, transactions, success=True):
        notifications = {
            "live": "false",
            "notificationItems": [
                cls._get_notification_item(transaction, success)
                for transaction in transactions
            ],
        }
        return notifications

    @classmethod
    def _get_payment_result_params(cls, transaction):
        params = {
            "cancel_redirect": "/cart/checkout?canceled_payment=adyen",
            "force_apply_redirection": "true",
            "redirectResult": "redirectResult",
            "success_redirect": "/cart/validation",
            "target": "current_cart",
            "transaction_id": transaction.id,
        }
        return params
