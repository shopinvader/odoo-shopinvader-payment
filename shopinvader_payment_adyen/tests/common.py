# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import Adyen
from Adyen.util import generate_notification_sig


class ShopinvaderAdyenCommon(object):
    @classmethod
    def setUpClass(cls):
        super(ShopinvaderAdyenCommon, cls).setUpClass()
        cls.shopinvader_payment = cls.env.ref(
            "shopinvader_payment_adyen.shopinvader_payment_adyen"
        )
        cls.account_payment_mode = cls.shopinvader_payment.payment_mode_id
        cls.account_payment_mode.payment_acquirer_id.adyen_skin_hmac_key = (
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

    def _get_adyen_service(cls):
        adyen = Adyen.Adyen(platform="test", live_endpoint_prefix="prefix")
        adyen.client.xapikey = "TEST"
        return adyen

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
        signature = generate_notification_sig(
            item["NotificationRequestItem"],
            transaction.acquirer_id.adyen_skin_hmac_key,
        )
        item["NotificationRequestItem"]["additionalData"][
            "hmacSignature"
        ] = signature
        return item

    def _get_notifications(cls, transactions, success=True):
        notifications = {
            "live": "false",
            "notificationItems": [
                cls._get_notification_item(transaction, success)
                for transaction in transactions
            ],
        }
        return notifications
