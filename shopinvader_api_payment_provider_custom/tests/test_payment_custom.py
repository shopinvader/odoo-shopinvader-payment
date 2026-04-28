# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from fastapi import status
from lxml.html import fromstring
from requests import Response

from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.tests.common import TestPaymentCommon

from ..routers.payment_custom import payment_router


class TestPaymentCustom(TestPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

        cls.custom_provider = cls.env.ref("payment.payment_provider_transfer")
        cls.custom_provider.is_published = True
        cls.custom_provider.state = "test"

        cls.custom_method = cls.env.ref("payment.payment_method_bank_transfer")
        cls.custom_provider.payment_method_ids = [cls.custom_method.id]
        cls.custom_method.active = True

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

    def test_custom_payment_transaction(self):
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "provider_id": self.custom_provider.id,
            "payment_method_id": self.custom_method.id,
            "frontend_redirect_url": "www.rtbf.be",
        }
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.post("/payment/transactions", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        res = response.json()
        self.assertEqual(res["provider_id"], self.custom_provider.id)
        self.assertEqual(res["provider_code"], self.custom_provider.code)
        self.assertEqual(res["reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(res["currency_id"], self.payable_rec.currency_id.id)
        self.assertEqual(res["partner_id"], self.payable_rec.partner_id.id)

        # Ensure a payment transaction was created
        tx = self.env["payment.transaction"].search(
            [("reference", "=", self.payable_rec.name)]
        )
        self.assertTrue(tx)
        self.assertEqual(tx.state, "draft")

        new_payable = (
            fromstring(res["redirect_form_html"])
            .xpath("//input[@name='payable']")[0]
            .get("value")
        )

        data = {
            "payable": new_payable,
            "frontend_redirect_url": "http://www.example.com",
        }
        with self._create_test_client(router=payment_router) as test_client:
            response: Response = test_client.post(
                "/payment/providers/custom/pending",
                data=data,
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER, response.text)
        self.assertIn("www.example.com", response.headers["Location"])
        self.assertEqual(tx.state, "pending")
