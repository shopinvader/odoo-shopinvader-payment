# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.test_invader_payment.tests.test_invader_payment_stripe import (
    TestInvaderPaymentStripe,
)


class TestShopinvaderPaymentStripe(TestInvaderPaymentStripe):
    def test_capture_payment(self):
        self.payment_mode.write({"capture_payment": "order_confirm"})
        result = self.service.dispatch(
            "confirm_payment",
            params={
                "target": "demo_partner",
                "payment_mode_id": self.payment_mode.id,
                "capture_mode": "manual",
                "stripe_payment_method_id": "pm_card_visa",
            },
        )
        self.assertEqual(result, {"success": True})
        self.sale_order = self.env["sale.order"].search(
            [
                ("partner_id", "=", self.demo_partner.id),
                ("typology", "=", "sale"),
                ("state", "=", "draft"),
            ]
        )
        transactions = self.sale_order.authorized_transaction_ids
        self.assertEqual(len(transactions) > 0, True)
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, "done")
        for transaction in transactions:
            self.assertEqual(transaction.state, "done")
