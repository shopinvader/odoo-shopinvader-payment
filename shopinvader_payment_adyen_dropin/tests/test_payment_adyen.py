# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from uuid import uuid4

import mock
from Adyen.client import AdyenResult
from Adyen.util import generate_notification_sig

from odoo import fields

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase

from .common import ShopinvaderAdyenDropInCommon

USAGE = "payment_adyen_dropin"


class TestShopinvaderAdyenService(
    ShopinvaderAdyenDropInCommon, CommonConnectedCartCase
):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage=USAGE)

    def test_payment_pending(self):
        # Select a SEPA payment method
        # Simulate a "Received" resultCode from Adyen
        # Check if cart has changed typology
        # Check if transaction is set to pending
        self.data.update({"acquirer_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        payable = self.cart
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                response = self.payment_service.dispatch(
                    "payments", params=self.data
                )
        transaction = payable.transaction_ids
        self.assertEqual(transaction.acquirer_reference, response.get("id"))
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            req_item = {
                "eventCode": "AUTHORISATION",
                "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
                "reason": "033899:1111:03/2030",
                "amount": {
                    "currency": transaction.currency_id.name,
                    "value": transaction._get_formatted_amount(),
                },
                "operations": ["CANCEL", "CAPTURE", "REFUND"],
                "success": "true",  # This define if the payment is ok
                "paymentMethod": "mc",
                "merchantReference": response.get("reference"),
                "pspReference": str(uuid4()).replace("-", "")[:16].upper(),
                "eventDate": fields.Datetime.now().isoformat(),
            }
            # Generate a valid signature with hmac
            merchant_sign = generate_notification_sig(
                req_item.copy(), self.acquirer.adyen_dropin_webhook_hmac
            )
            hmac_signature = merchant_sign.decode("utf-8")
            req_item.update(
                {
                    "additionalData": {
                        "expiryDate": "03/2030",
                        "authCode": "033899",
                        "cardBin": "411111",
                        "cardSummary": "1111",
                        "checkoutSessionId": response.get("id"),
                        "hmacSignature": hmac_signature,
                    },
                }
            )
            fake_response = {
                "live": "false",
                "notificationItems": [
                    {
                        "NotificationRequestItem": req_item,
                    }
                ],
            }
            res = self.payment_service.dispatch(
                "webhook", params=fake_response
            )
        self.assertEqual("[accepted]", res)
        self.assertEqual("done", transaction.state)
        self.assertEqual("sale", self.cart.typology)

    def test_payment_done(self):
        # Select a Credit Card payment method
        # Simulate a "Authorized" resultCode from Adyen
        # Check if cart has changed typology
        # Check if transaction is set to done
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        payable = self.cart
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                response = self.payment_service.dispatch(
                    "payments", params=self.data
                )
        transaction = payable.transaction_ids
        self.assertTrue(transaction)
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(adyen.checkout, "payments") as mock_payment:
                mock_payment.return_value = self.payments_response_scheme
                req_item = {
                    "eventCode": "AUTHORISATION",
                    "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
                    "reason": "033899:1111:03/2030",
                    "amount": {
                        "currency": transaction.currency_id.name,
                        "value": transaction._get_formatted_amount(),
                    },
                    "operations": ["CANCEL", "CAPTURE", "REFUND"],
                    "success": "true",  # This define if the payment is ok
                    "paymentMethod": "mc",
                    "merchantReference": response.get("reference"),
                    "pspReference": str(uuid4()).replace("-", "")[:16].upper(),
                    "eventDate": fields.Datetime.now().isoformat(),
                }
                # Generate a valid signature with hmac
                merchant_sign = generate_notification_sig(
                    req_item.copy(), self.acquirer.adyen_dropin_webhook_hmac
                )
                hmac_signature = merchant_sign.decode("utf-8")
                req_item.update(
                    {
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": response.get("id"),
                            "hmacSignature": hmac_signature,
                        },
                    }
                )
                fake_response = {
                    "live": "false",
                    "notificationItems": [
                        {
                            "NotificationRequestItem": req_item,
                        }
                    ],
                }
                res = self.payment_service.dispatch(
                    "webhook", params=fake_response
                )

        self.assertEqual("[accepted]", res)
        self.assertEqual("done", transaction.state)
        self.assertEqual("sale", self.cart.typology)
        # Simulate the cron
        transaction._post_process_after_done()
        self.assertEqual("sale", self.cart.state)

    def _get_return_value(self):
        result = AdyenResult()
        result.message = {
            "pspReference": "test",
            "additionalData": {"paymentMethod": "visa"},
            "resultCode": "Authorised",
        }
        return result

    def test_notification(self):
        self.data.update({"acquirer_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        payable = self.cart
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            res = self.payment_service.dispatch("payments", params=self.data)
        self.transaction = payable.transaction_ids
        self.assertEqual(self.transaction.acquirer_reference, res.get("id"))
        request = self._get_notifications(self.transaction)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage=USAGE)
        self.assertEqual("pending", self.transaction.state)
        result = self.service.dispatch("webhook", params=request)
        self.assertEqual("[accepted]", result)
        self.assertEqual("done", self.transaction.state)
        self.assertEqual(res.get("id"), self.transaction.acquirer_reference)

    def test_notification_other(self):
        """
        Check something else than AUTHORISATION
        """
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        payable = self.cart
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            res = self.payment_service.dispatch("payments", params=self.data)
        self.transaction = payable.transaction_ids
        self.assertEqual(self.transaction.acquirer_reference, res.get("id"))
        request = self._get_notifications(self.transaction)
        items = request["notificationItems"]
        item = items[0]["NotificationRequestItem"]
        item["eventCode"] = "REPORT_AVAILABLE"
        # As the content has been edited, re-generate the signature
        self._regenerate_signature(request)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage=USAGE)
        self.assertEqual("pending", self.transaction.state)
        result = self.service.dispatch("webhook", params=request)
        # Error because event not supported
        self.assertEqual("[error]", result)
        self.assertEqual("pending", self.transaction.state)

    def test_notification_failed(self):
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        payable = self.cart
        with mock.patch.object(
            self.payment_service, "_get_service"
        ) as mock_adyen:
            adyen = self._get_service()
            mock_adyen.return_value = adyen
            res = self.payment_service.dispatch("payments", params=self.data)
        self.transaction = payable.transaction_ids
        self.assertEqual(self.transaction.acquirer_reference, res.get("id"))
        request = self._get_notifications(self.transaction, success=False)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage=USAGE)
        self.assertEqual("pending", self.transaction.state)
        self.service.dispatch("webhook", params=request)

        self.assertEqual("error", self.transaction.state)
