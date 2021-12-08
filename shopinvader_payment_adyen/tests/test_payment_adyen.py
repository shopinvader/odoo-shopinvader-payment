# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import Adyen
import mock
from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


def _get_adyen_service():
    adyen = Adyen.Adyen(
        app_name="TEST", platform="test", live_endpoint_prefix="prefix"
    )
    adyen.client.xapikey = "TEST"
    return adyen


class TestShopinvaderAdyenService(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(TestShopinvaderAdyenService, self).setUp(*args, **kwargs)
        self.shopinvader_payment = self.env.ref(
            "shopinvader_payment_adyen.shopinvader_payment_adyen"
        )
        self.account_payment_mode = self.shopinvader_payment.payment_mode_id
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_adyen")

        self.data = {"target": "current_cart"}
        # https://docs.adyen.com/checkout/drop-in-web#-paymentmethods-response
        vals = {
            "paymentMethods": [
                {"name": "SEPA", "type": "sepadirectdebit"},
                {"name": "Credit Card", "type": "scheme"},
            ]
        }
        self.payment_method_response = Adyen.client.AdyenResult(message=vals)
        vals = {
            "pspReference": "881572960484022G",
            "resultCode": "Received",
            "merchantReference": "YOUR_ORDER_NUMBER",
        }
        self.payments_response = Adyen.client.AdyenResult(message=vals)

    def test_payment_pending(self):
        # Select a SEPA payment method
        # Simulate a "Received" resultCode from Adyen
        # Check if cart has changed typology
        # Check if transaction is set to pending
        self.data.update({"payment_mode_id": self.account_payment_mode.id})
        self.assertEquals("cart", self.cart.typology)
        with mock.patch.object(
            self.payment_service, "_get_adyen_service"
        ) as mock_adyen:
            adyen = _get_adyen_service()
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
            adyen = _get_adyen_service()
            mock_adyen.return_value = adyen
            with mock.patch.object(adyen.checkout, "payments") as mock_payment:
                mock_payment.return_value = self.payments_response
                self.data.update(
                    {
                        "transaction_id": transaction_id,
                        "payment_mode_id": self.account_payment_mode.id,
                        "payment_method": sepa,
                        "return_url": "https://dummy",
                    }
                )
                res = self.payment_service.dispatch(
                    "payments", params=self.data
                )

        code = res.get("resultCode")
        self.assertEquals("Received", code)
        transaction = self.env["payment.transaction"].browse(transaction_id)
        self.assertEquals("pending", transaction.state)
        self.assertEquals("sale", self.cart.typology)
