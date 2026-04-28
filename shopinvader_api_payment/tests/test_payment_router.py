# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from fastapi import status
from requests import Response

from ..routers import payment_router
from ..routers.utils import Payable
from .common import TestPaymentCommon


class TestPaymentCart(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.init_provider()

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

    def test_get_payment_methods(self):
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.get(
                f"/payment/methods?payable={self.encoded_payable}"
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.json()
        self.assertEqual(res["payable"], self.encoded_payable)
        self.assertEqual(res["payable_reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(
            res["amount_formatted"],
            self.payable_rec.currency_id.format(self.payable_rec.amount),
        )
        providers = res["providers"]
        self.assertEqual(len(providers), 1)
        provider = providers[0]
        self.assertEqual(provider["id"], self.demo_provider.id)
        methods = provider["payment_methods"]
        self.assertEqual(len(methods), 2)
        method_ids = {method["id"] for method in methods}
        self.assertIn(self.demo_method_1.id, method_ids)
        self.assertIn(self.demo_method_2.id, method_ids)

    def test_create_payment_transaction(self):
        """
        Create payment transaction having chosen demo provider
        """
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "provider_id": self.demo_provider.id,
            "payment_method_id": self.demo_method_1.id,
            "frontend_redirect_url": "www.rtbf.be",
        }
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.post("/payment/transactions", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        res = response.json()
        self.assertEqual(res["provider_id"], self.demo_provider.id)
        self.assertEqual(res["provider_code"], self.demo_provider.code)
        self.assertEqual(res["reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(res["currency_id"], self.payable_rec.currency_id.id)
        self.assertEqual(res["partner_id"], self.payable_rec.partner_id.id)

        # Ensure a payment transaction was created
        self.assertTrue(
            self.env["payment.transaction"].search(
                [("reference", "=", self.payable_rec.name)]
            )
        )
