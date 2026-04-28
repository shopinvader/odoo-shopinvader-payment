# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from fastapi import status
from requests import Response

from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.tests.common import TestPaymentCommon

from ..routers.payment_stripe import payment_router


class TestPaymentStripe(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

        cls.stripe_provider = cls.env.ref("payment.payment_provider_stripe")
        cls.stripe_provider.write(
            {
                "state": "test",
                "is_published": True,
                "stripe_secret_key": "sk_test_KJtHgNwt2KS3xM7QJPr4O5E8",
                "stripe_publishable_key": "pk_test_QSPnimmb4ZhtkEy3Uhdm4S6J",
                "stripe_webhook_secret": "whsec_vG1fL6CMUouQ7cObF2VJprLVXT5jBLxB",
            }
        )

        cls.stripe_method_1 = cls.env.ref("payment.payment_method_paypal")

        cls.stripe_method_2 = cls.env.ref("payment.payment_method_card")

        cls.stripe_provider.payment_method_ids = [
            cls.stripe_method_1.id,
            cls.stripe_method_2.id,
        ]
        cls.stripe_method_1.write({"active": True})
        cls.stripe_method_2.write({"active": True})

    def setUp(self) -> None:
        super().setUp()
        self.payable_rec = self._create_payable_record(self.partner)
        payable = Payable(
            payable_id=self.payable_rec.id,
            payable_model="payable.test.model",
            payable_reference=self.payable_rec.name,
            amount=self.payable_rec.amount,
            currency_id=self.payable_rec.currency_id.id,
            partner_id=self.payable_rec.partner_id.id,
            company_id=self.payable_rec.company_id.id,
        )
        self.encoded_payable = payable.encode(self.env)

    def test_stripe_payment_transaction(self):
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "provider_id": self.stripe_provider.id,
            "payment_method_id": self.stripe_method_1.id,
            "frontend_redirect_url": "https://www.example.com",
        }
        payment_method_response = {
            "card": {"last4": "4242"},
            "id": "pm_1KVZSNAlCFm536g8sYB92I1G",
            "type": "card",
        }

        def mock_stripe_stripe_create_intent(self):
            return {"client_secret": "secret"}

        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_stripe.controllers.main.StripeController"
                "._verify_notification_signature"
            ),
            patch(
                "odoo.addons.payment_stripe.models.payment_provider.PaymentProvider"
                "._stripe_make_request",
                return_value=payment_method_response,
            ),
            patch.object(
                type(self.env["payment.transaction"]),
                "_stripe_create_intent",
                mock_stripe_stripe_create_intent,
            ),
        ):
            response: Response = test_client.post("/payment/transactions", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        res = response.json()
        self.assertEqual(res["provider_id"], self.stripe_provider.id)
        self.assertEqual(res["provider_code"], self.stripe_provider.code)
        self.assertEqual(res["reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(res["currency_id"], self.payable_rec.currency_id.id)
        self.assertEqual(res["partner_id"], self.payable_rec.partner_id.id)
        self.assertIn("stripe/checkout_return", res["return_url"])
        self.assertIn("redirect_url=", res["return_url"])
        self.assertIn("www.example.com", res["return_url"])

        # Ensure a payment transaction was created
        tx = self.env["payment.transaction"].search(
            [("reference", "=", self.payable_rec.name)]
        )
        self.assertTrue(tx)
        self.assertEqual(tx.state, "draft")

        data = {
            "reference": self.payable_rec.name,
            "redirect_url": "https://www.example.com/redirect",
        }
        payment_response = {
            "card": {"last4": "4242"},
            "type": "card",
            "id": "pm_1KVZSNAlCFm536g8sYB92I1G",
            "status": "pending",
        }

        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_stripe.models.payment_provider.PaymentProvider"
                "._stripe_make_request",
                return_value=payment_response,
            ),
        ):
            response: Response = test_client.get(
                "/payment/providers/stripe/checkout_return",
                params=data,
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER, response.text)
        self.assertIn("www.example.com/redirect", response.headers["Location"])
        self.assertEqual(tx.state, "pending")
