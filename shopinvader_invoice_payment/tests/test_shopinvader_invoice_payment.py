# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopinvader_invoice.tests.common import CommonInvoiceCase


class TestShopinvaderInvoicePayment(CommonInvoiceCase):
    def setUp(self, *args, **kwargs):
        super(TestShopinvaderInvoicePayment, self).setUp(*args, **kwargs)
        self.register_payments_obj = self.env["account.register.payments"]
        self.journal_obj = self.env["account.journal"]
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        self.bank_journal_euro = self.journal_obj.create(
            {"name": "Bank", "type": "bank", "code": "BNK6278"}
        )
        self.invoice = self._confirm_and_invoice_sale(self.sale, payment=False)
        self.payment_mode = self.env.ref(
            "invader_payment_manual.payment_mode_check"
        )
        with self.work_on_services(partner=self.partner) as work:
            self.payment_manual_service = work.component(
                usage="payment_manual"
            )

    def _check_number_of_payment_mode(self, response, expected_number):
        self.assertIn("available_methods", response["data"][0]["payment"])
        self.assertEqual(
            response["data"][0]["payment"]["available_methods"]["count"],
            expected_number,
        )

    def test_get_no_invoice_payment_info(self):
        """
        Retrieve invoice info.
        As no available methods set, the result should contains any.
        :return:
        """
        self.backend.write({"payment_method_ids": [(5, False, False)]})
        response = self.service.dispatch("search")
        self.assertEqual(
            response["data"][0]["payment"]["available_methods"]["count"], 0
        )
        return

    def test_invoice_payment_info(self):
        """
        Retrieve the invoice information.
        Ensure available methods are ones set on the backend
        :return:
        """
        response = self.service.dispatch(
            "search", params={"id": self.invoice.id}
        )
        self._check_number_of_payment_mode(
            response, len(self.backend.payment_method_ids)
        )

    def test_pay_invoice_with_check(self):
        self.assertEqual(self.invoice.state, "open")
        residual = self.invoice.residual
        self.payment_manual_service.dispatch(
            "add_payment",
            params={
                "target": "invoice",
                "invoice_id": self.invoice.id,
                "payment_mode_id": self.payment_mode.id,
            },
        )
        # Still open because the manual payment doesn't validate the invoice
        self.assertEqual(self.invoice.state, "open")
        self.assertEqual(len(self.invoice.transaction_ids), 1)
        transaction = self.invoice.transaction_ids
        self.assertIn(self.invoice.number, transaction.reference)
        self.assertEqual(
            self.payment_mode.payment_acquirer_id, transaction.acquirer_id
        )
        self.assertAlmostEqual(
            residual, transaction.amount, places=self.precision
        )
