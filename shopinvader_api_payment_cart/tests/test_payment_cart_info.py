# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from fastapi import status
from requests import Response

from odoo.addons.shopinvader_api_cart.routers import cart_router
from odoo.addons.shopinvader_api_cart.tests.common import CommonSaleCart
from odoo.addons.shopinvader_api_payment.routers.utils import Payable


class TestPaymentCart(CommonSaleCart):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_current_cart_payable_info(self):
        so = self.env["sale.order"]._create_empty_cart(
            self.default_fastapi_authenticated_partner.id
        )
        with self._create_test_client(router=cart_router) as test_client:
            response: Response = test_client.get("/current/payable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.json()
        decoded_payable = Payable.decode(self.env, res["payable"])
        self.assertEqual(decoded_payable.payable_model, "sale.order")
        self.assertEqual(decoded_payable.payable_id, so.id)
        self.assertEqual(res["payable_reference"], so.name)
        self.assertEqual(res["amount"], so.amount_total)

    def test_get_cart_via_uuid_payable_info(self):
        so = self.env["sale.order"]._create_empty_cart(
            self.default_fastapi_authenticated_partner.id
        )
        with self._create_test_client(router=cart_router) as test_client:
            response: Response = test_client.get(f"/{so.uuid}/payable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = response.json()
        decoded_payable = Payable.decode(self.env, res["payable"])
        self.assertEqual(decoded_payable.payable_model, "sale.order")
        self.assertEqual(decoded_payable.payable_id, so.id)
        self.assertEqual(res["payable_reference"], so.name)
        self.assertEqual(res["amount"], so.amount_total)

    def test_get_cart_payable_no_cart(self):
        with self._create_test_client(router=cart_router) as test_client:
            response: Response = test_client.get("/current/payable")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
