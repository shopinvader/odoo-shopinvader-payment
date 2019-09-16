# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock
from odoo.addons.shopinvader_invoice_payment.tests.common import (
    CommonCaseShopinvaderInvoice,
)
from odoo.addons.shopinvader_payment_adyen.tests.test_payment import (
    ShopinvaderAdyenCommonCase,
)
from odoo.exceptions import UserError


class ShopinvaderPaymentAdyenCase(
    CommonCaseShopinvaderInvoice, ShopinvaderAdyenCommonCase
):
    def setUp(self, *args, **kwargs):
        self.invoice_obj = self.env["account.invoice"]
        # The workflow do an exclusive lock and block tests. So mock it!
        from odoo import workflow

        with mock.patch.object(workflow, "trg_create"):
            super(ShopinvaderPaymentAdyenCase, self).setUp(*args, **kwargs)
            ShopinvaderAdyenCommonCase.setUp(self, *args, **kwargs)
            self.account_payment_mode = self.env.ref(
                "payment_gateway_adyen.account_payment_mode_adyen"
            )
            with self.work_on_services(
                partner=self.service.partner,
                shopinvader_session=self.service.shopinvader_session,
            ) as work:
                self.service = work.component(usage="invoice")
            self.invoice_obj = self.env["account.invoice"]
            self.invoice_line_obj = self.env["account.invoice.line"]
            self.invoice = self._create_invoice(partner=self.service.partner)
            self._create_invoice_line(self.invoice, product=self.product1)
            self._create_invoice_line(self.invoice, product=self.product2)

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
        card = self._get_card("5100290029002909")
        adyen_params = self._prepare_transaction_params(card)
        params = {
            "id": str(self.invoice.id),
            "payment_mode": {"id": self.account_payment_mode.id},
            "adyen": adyen_params,
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
