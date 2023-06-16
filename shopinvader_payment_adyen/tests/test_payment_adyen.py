# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock
from Adyen.client import AdyenResult

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase

from .common import ShopinvaderAdyenCommon


class TestShopinvaderAdyenService(
    ShopinvaderAdyenCommon, CommonConnectedCartCase
):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_adyen")

    def test_payment_pending(self):
        # Select a SEPA payment method
        # Simulate a "Received" resultCode from Adyen
        # Check if cart has changed typology
        # Check if transaction is set to pending
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        transaction_id = res.get("transaction_id")
        methods = res.get("paymentMethods")
        sepa = [
            method
            for method in methods
            if method.get("type") == "sepadirectdebit"
        ][0]
        self.assertTrue(sepa)
        self.assertTrue(transaction_id)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(adyen.checkout, "payments") as mock_payment:
                mock_payment.return_value = self.payments_response
                self.data.update(
                    {
                        "transaction_id": transaction_id,
                        "payment_mode_id": self.acquirer.id,
                        "payment_method": sepa,
                        "return_url": "https://dummy",
                    }
                )
                res = self.payment_service.dispatch(
                    "payments", params=self.data
                )

        code = res.get("resultCode")
        self.assertEqual("Received", code)
        transaction = self.env["payment.transaction"].browse(transaction_id)
        self.assertEqual("pending", transaction.state)
        self.assertEqual("sale", self.cart.typology)

    def test_payment_done(self):
        # Select a Credit Card payment method
        # Simulate a "Authorized" resultCode from Adyen
        # Check if cart has changed typology
        # Check if transaction is set to done
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        transaction_id = res.get("transaction_id")
        methods = res.get("paymentMethods")
        scheme = [
            method for method in methods if method.get("type") == "scheme"
        ][0]
        self.assertTrue(scheme)
        self.assertTrue(transaction_id)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(adyen.checkout, "payments") as mock_payment:
                mock_payment.return_value = self.payments_response_scheme
                self.data.update(
                    {
                        "transaction_id": transaction_id,
                        "payment_mode_id": self.acquirer.id,
                        "payment_method": scheme,
                        "return_url": "https://dummy",
                    }
                )
                res = self.payment_service.dispatch(
                    "payments", params=self.data
                )

        code = res.get("resultCode")
        self.assertEqual("Authorised", code)
        transaction = self.env["payment.transaction"].browse(transaction_id)
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
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        self.transaction = self.env["payment.transaction"].browse(
            res.get("transaction_id")
        )
        request = self._get_notifications(self.transaction)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage="payment_adyen")
        self.assertEqual("draft", self.transaction.state)
        result = self.service.dispatch("webhook", params=request)
        self.assertEqual("[accepted]", result)
        self.assertEqual("done", self.transaction.state)
        self.assertEqual(
            "psp_reference_1", self.transaction.acquirer_reference
        )

    def test_notification_other(self):
        """
        Check something else than AUTHORISATION
        """
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        self.transaction = self.env["payment.transaction"].browse(
            res.get("transaction_id")
        )
        request = self._get_notifications(self.transaction)
        items = request["notificationItems"]
        item = items[0]["NotificationRequestItem"]
        item["eventCode"] = "REPORT_AVAILABLE"
        # As the content has been edited, re-generate the signature
        self._regenerate_signature(request)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage="payment_adyen")
        self.assertEqual("draft", self.transaction.state)
        result = self.service.dispatch("webhook", params=request)
        self.assertEqual("[accepted]", result)
        self.assertEqual("draft", self.transaction.state)

    def test_notification_failed(self):
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        self.transaction = self.env["payment.transaction"].browse(
            res.get("transaction_id")
        )
        request = self._get_notifications(self.transaction, success=False)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage="payment_adyen")
        self.assertEqual("draft", self.transaction.state)
        self.service.dispatch("webhook", params=request)

        self.assertEqual("error", self.transaction.state)

    def test_payment_result(self):
        self.data.update({"payment_mode_id": self.acquirer.id})
        self.assertEqual("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payment_methods"
            ) as mock_methods:
                result = self.payment_method_response
                mock_methods.return_value = result
                res = self.payment_service.dispatch(
                    "paymentMethods", params=self.data
                )
        self.transaction = self.env["payment.transaction"].browse(
            res.get("transaction_id")
        )
        self.assertEqual("draft", self.transaction.state)
        params = self._get_payment_result_params(self.transaction)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = self._get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(
                adyen.checkout, "payments_details"
            ) as mock_methods:
                result = self.payments_response_scheme
                mock_methods.return_value = result
                result = self.payment_service.dispatch(
                    "paymentResult", params=params
                )
