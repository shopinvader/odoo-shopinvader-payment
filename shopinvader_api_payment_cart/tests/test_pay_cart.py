# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from fastapi import status
from requests import Response

from odoo.addons.shopinvader_api_payment.routers import payment_router
from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.tests.common import TestPaymentCommon


class TestPayCart(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.demo_provider = cls.env.ref("payment.payment_provider_demo")
        cls.demo_provider.write({"state": "test", "is_published": True})

        cls.cart = cls.env["sale.order"]._create_empty_cart(
            cls.env["res.partner"].create({"name": "Customer"}).id,
        )
        # Default payable token:
        payable = Payable(
            payable_id=cls.cart.id,
            payable_model="sale.order",
            payable_reference=cls.cart.name,
            amount=cls.cart.amount_total,
            currency_id=cls.cart.currency_id.id,
            partner_id=cls.cart.partner_id.id,
            company_id=cls.cart.company_id.id,
        )
        cls.encoded_payable = payable.encode(cls.env)

    def test_get_payment_methods_wrong_payable(self):
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.get(
                "/payment/methods?payable=wrongPayable"
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_payment_methods(self):
        """
        Demo provider was activated in shopinvader_api_payment common test class.
        Check that it is returned by payment/methods
        """
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.get(
                f"/payment/methods?payable={self.encoded_payable}"
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.json()
        self.assertEqual(res["payable"], self.encoded_payable)
        self.assertEqual(res["payable_reference"], self.cart.name)
        self.assertEqual(res["amount"], self.cart.amount_total)
        self.assertEqual(
            res["amount_formatted"],
            self.cart.currency_id.format(self.cart.amount_total),
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
        self.assertEqual(res["reference"], self.cart.name)
        self.assertEqual(res["amount"], self.cart.amount_total)
        self.assertEqual(res["currency_id"], self.cart.currency_id.id)
        self.assertEqual(res["partner_id"], self.cart.partner_id.id)

        # Ensure a payment transaction was created and linked to the cart
        tx = self.env["payment.transaction"].search(
            [("reference", "=", self.cart.name)]
        )
        self.assertEqual(len(tx), 1)
        self.assertEqual(tx.sale_order_ids, self.cart)
