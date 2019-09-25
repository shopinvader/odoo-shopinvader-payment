# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError

from .common import TestCommonPayment


class TestInvaderPaymentManual(TestCommonPayment):
    def setUp(self):
        super(TestInvaderPaymentManual, self).setUp()
        self.payment_mode = self.env.ref(
            "invader_payment_manual.payment_mode_check"
        )
        self.service = self._get_service("payment_manual")

    def test_add_payment(self):
        existing_transactions = self.env["payment.transaction"].search(
            [("acquirer_id", "=", self.payment_mode.payment_acquirer_id.id)]
        )
        self.service.dispatch(
            "add_payment",
            params={
                "target": "demo_partner",
                "payment_mode_id": self.payment_mode.id,
            },
        )
        transaction = self.env["payment.transaction"].search(
            [
                ("acquirer_id", "=", self.payment_mode.payment_acquirer_id.id),
                ("id", "not in", existing_transactions.ids),
            ]
        )
        self.assertEqual(len(transaction), 1)
        self.assertEqual(transaction.state, "pending")

    def test_wrong_provider_add_payment(self):
        self.payment_mode_stripe = self.env.ref(
            "invader_payment_stripe.payment_mode_stripe"
        )
        with self.assertRaises(UserError) as m:
            self.service.dispatch(
                "add_payment",
                params={
                    "target": "demo_partner",
                    "payment_mode_id": self.payment_mode_stripe.id,
                },
            )
        self.assertEqual(
            m.exception.name,
            _(
                "Payment mode acquirer mismatch should be "
                "'transfer' instead of 'stripe'."
            ),
        )
