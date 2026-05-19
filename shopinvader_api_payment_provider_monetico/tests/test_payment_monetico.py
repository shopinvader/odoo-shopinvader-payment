# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from fastapi import status
from requests import Response

from odoo.addons.payment_monetico.tests.common import MoneticoCommon
from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.tests.common import TestPaymentCommon

from ..routers.payment_monetico import payment_router


class TestPaymentMonetico(TestPaymentCommon, MoneticoCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

        cls.monetico_provider = cls.monetico
        cls.monetico_provider.write(
            {
                "is_published": True,
            }
        )

        cls.monetico_method_1 = cls.env.ref("payment.payment_method_card")
        cls.monetico_method_2 = cls.env.ref("payment.payment_method_visa")
        cls.monetico_method_3 = cls.env.ref("payment_monetico.payment_method_cb")

        cls.monetico_provider.payment_method_ids = [
            cls.monetico_method_1.id,
            cls.monetico_method_2.id,
            cls.monetico_method_3.id,
        ]

        cls.monetico_method_1.write({"active": True})
        cls.monetico_method_2.write({"active": True})
        cls.monetico_method_3.write({"active": True})

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

    def test_monetico_payment_transaction(self):
        data = {
            "payable": self.encoded_payable,
            "flow": "redirect",
            "provider_id": self.monetico_provider.id,
            "payment_method_id": self.monetico_method_1.id,
            "frontend_redirect_url": "https://www.example.com",
        }

        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_monetico.controllers.main.MoneticoController"
                "._verify_notification_signature"
            ),
        ):
            response: Response = test_client.post("/payment/transactions", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        res = response.json()
        self.assertEqual(res["provider_id"], self.monetico_provider.id)
        self.assertEqual(res["provider_code"], self.monetico_provider.code)
        self.assertEqual(res["reference"], self.payable_rec.name)
        self.assertEqual(res["amount"], self.payable_rec.amount)
        self.assertEqual(res["currency_id"], self.payable_rec.currency_id.id)
        self.assertEqual(res["partner_id"], self.payable_rec.partner_id.id)
        self.assertIn("/payment/providers/monetico/return", res["redirect_form_html"])

        # Ensure a payment transaction was created
        tx = self.env["payment.transaction"].search(
            [("reference", "=", self.payable_rec.name)]
        )
        self.assertTrue(tx)
        self.assertEqual(tx.state, "draft")

        data = {
            "reference": self.payable_rec.name,
            "MAC": "12",
            "code-retour": "payetest",
        }

        with (
            self._create_test_client(router=payment_router) as test_client,
            patch(
                "odoo.addons.payment_monetico.controllers.main.MoneticoController"
                "._verify_notification_signature"
            ),
        ):
            response: Response = test_client.post(
                "/payment/providers/monetico/return",
                data=data,
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER, response.text)
        self.assertIn("www.example.com", response.headers["Location"])
        self.assertEqual(tx.state, "done")
