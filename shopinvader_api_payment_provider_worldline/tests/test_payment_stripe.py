# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from fastapi import status
from requests import Response

from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.tests.common import TestPaymentCommon

from ..routers.payment_worldline import payment_router


class TestPaymentWorldline(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

        cls.worldline_provider = cls.env.ref("payment.payment_provider_worldline")
        cls.worldline_provider.write(
            {
                "state": "test",
                "is_published": True,
                "worldline_pspid": "dummy",
                "worldline_api_key": "dummy",
                "worldline_api_secret": "dummy",
                "worldline_webhook_key": "dummy",
                "worldline_webhook_secret": "dummy",
            }
        )

        cls.worldline_method_1 = cls.env.ref("payment.payment_method_paypal")

        cls.worldline_method_2 = cls.env.ref("payment.payment_method_card")

        cls.worldline_provider.payment_method_ids = [
            cls.worldline_method_1.id,
            cls.worldline_method_2.id,
        ]
        cls.worldline_method_1.write({"active": True})
        cls.worldline_method_2.write({"active": True})

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

    def test_worldline_payment_transaction(self):
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "method_id": self.worldline_method_1.id,
            "frontend_redirect_url": "https://www.example.com",
        }

        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_worldline.models.payment_provider.PaymentProvider."
                "_worldline_make_request",
                return_value={
                    "redirectUrl": "https://payment-redirect.com?transaction=123",
                    "id": "hosted_checkout_id_123",
                },
            ) as worldline_make_request_mock,
        ):
            response: Response = test_client.post("/payment/transactions", json=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        res = response.json()
        self.assertEqual(res["provider_id"], self.worldline_provider.id)
        self.assertEqual(res["provider_code"], self.worldline_provider.code)
        self.assertEqual(res["reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(res["currency_id"], self.payable_rec.currency_id.id)
        self.assertEqual(res["partner_id"], self.payable_rec.partner_id.id)

        self.assertEqual(worldline_make_request_mock.call_count, 1)
        payload = worldline_make_request_mock.call_args.kwargs["payload"]
        self.assertIn("hostedCheckoutSpecificInput", payload)
        self.assertIn(
            "/payment/providers/worldline/return"
            f"?provider_id={self.worldline_provider.id}",
            payload["hostedCheckoutSpecificInput"]["returnUrl"],
        )
        self.assertIn("redirectPaymentMethodSpecificInput", payload)
        self.assertIn(
            "/payment/providers/worldline/return"
            f"?provider_id={self.worldline_provider.id}",
            payload["redirectPaymentMethodSpecificInput"]["redirectionData"][
                "returnUrl"
            ],
        )

        # Ensure a payment transaction was created
        tx = self.env["payment.transaction"].search(
            [("reference", "=", self.payable_rec.name)]
        )
        self.assertTrue(tx)
        self.assertEqual(tx.state, "draft")

        data = {
            "hostedCheckoutId": "hosted_checkout_id_123",
            "provider_id": self.worldline_provider.id,
        }
        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_worldline.models.payment_provider.PaymentProvider."
                "_worldline_make_request",
                return_value={
                    "createdPaymentOutput": {
                        "id": "hosted_checkout_id_123",
                        "paymentResult": {
                            "payment": {
                                "paymentOutput": {
                                    "references": {
                                        "merchantReference": self.payable_rec.name
                                    }
                                },
                                "status": "PENDING_CAPTURE",
                            }
                        },
                    },
                },
            ) as worldline_make_request_mock,
        ):
            response: Response = test_client.get(
                "/payment/providers/worldline/return",
                params=data,
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER, response.text)
        self.assertEqual(
            response.headers["Location"],
            f"https://www.example.com?status=pending&reference={self.payable_rec.name}",
        )
        self.assertEqual(tx.state, "pending")
