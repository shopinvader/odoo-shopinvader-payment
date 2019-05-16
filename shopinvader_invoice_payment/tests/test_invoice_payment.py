# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError

from .common import CommonCaseShopinvaderInvoice


class ShopinvaderPaymentCase(CommonCaseShopinvaderInvoice):
    def test_get_invoice_payment_info(self):
        self.invoice.action_invoice_open()
        response = self.service.dispatch("search")
        all_data = response.get("data", [])
        self.assertTrue(all_data)
        for data in all_data:
            payment = data.get("payment", {})
            self.assertIn("available_methods", payment)
            self.assertEqual(
                payment.get("available_methods", {}).get("count", 0),
                len(self.backend.payment_method_ids),
            )
        return

    def test_add_check_payment(self):
        self.invoice.action_invoice_open()
        self.assertEquals(self.invoice.state, "open")
        self.assertNotEquals(
            self.invoice.payment_mode_id, self.account_payment_mode
        )
        params = {
            "id": str(self.invoice.id),
            "payment_mode": {"id": self.account_payment_mode.id},
        }
        self.service.dispatch("add_payment", params=params)
        self.assertEquals(
            self.invoice.payment_mode_id, self.account_payment_mode
        )
        return

    def test_no_check_payment(self):
        self.invoice.action_invoice_open()
        params = {
            "id": str(self.invoice.id),
            "payment_mode": {"id": self.account_payment_mode.id},
        }
        self.env.ref("shopinvader_payment.shopinvader_payment_check").unlink()
        with self.assertRaises(UserError):
            self.service.dispatch("add_payment", params=params)
        return

    def test_return_url(self):
        provider = "my-provider"
        url = self.service._get_return_url(provider)
        expected_url = (
            u"http://locomotive:3000/"
            u"invader/invoice/check_payment/%s" % provider
        )
        self.assertEqual(url, expected_url)
