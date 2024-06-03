# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from fastapi import status
from requests import Response

from odoo.addons.shopinvader_api_payment.routers.utils import Payable

from ..routers.payment import payment_router
from .common import TestPaymentCommon


class TestPaymentCart(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner = cls.env["res.partner"].create({"name": "Customer"})
        cls.payable_rec = cls._create_payable_record(partner)
        payable = Payable(
            payable_id=cls.payable_rec.id,
            payable_model="payable.test.model",
            payable_reference=cls.payable_rec.name,
            amount=cls.payable_rec.amount,
            currency_id=cls.payable_rec.currency_id.id,
            partner_id=cls.payable_rec.partner_id.id,
            company_id=cls.payable_rec.company_id.id,
        )
        cls.encoded_payable = payable.encode(cls.env)

        cls.demo_provider = cls.env.ref("payment.payment_provider_demo")
        cls.demo_provider.write({"state": "test", "is_published": True})

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
        self.assertEqual(providers[0]["id"], self.demo_provider.id)

    def test_create_payment_transaction(self):
        """
        Create payment transaction having chosen demo provider
        """
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "provider_id": self.demo_provider.id,
            "frontend_redirect_url": "www.rtbf.be",
        }
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.post(
                "/payment/transactions", content=json.dumps(data)
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
