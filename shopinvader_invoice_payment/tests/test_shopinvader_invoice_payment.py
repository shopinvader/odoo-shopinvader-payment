# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopinvader_invoice.tests.common import CommonInvoiceCase
from odoo.addons.shopinvader_payment.tests.common import CommonPaymentCase


# Keep that order as setup will fail either
class TestShopinvaderInvoicePayment(CommonPaymentCase, CommonInvoiceCase):
    def _set_transaction(self):
        self.transaction = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.acquirer_electronic.id,
                "amount": self.invoice.amount_total,
                "currency_id": self.invoice.currency_id.id,
                "invoice_ids": [(6, 0, self.invoice.ids)],
            }
        )

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.journal_obj = self.env["account.journal"]
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        self.bank_journal_euro = self.journal_obj.create(
            {"name": "Bank", "type": "bank", "code": "BNK6278"}
        )
        self.invoice = self._confirm_and_invoice_sale(self.sale, payment=False)
        self.backend.write({"invoice_access_open": True})
        with self.work_on_services(partner=self.partner) as work:
            self.payment_manual_service = work.component(
                usage="fake_payment_manual"
            )
        with self.work_on_services(partner=self.partner) as work:
            self.payment_electronic_service = work.component(
                usage="fake_payment_electronic"
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
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.invoice.payment_state, "not_paid")
        residual = self.invoice.amount_residual
        self.payment_manual_service.dispatch(
            "add_payment",
            params={
                "target": "invoice",
                "invoice_id": self.invoice.id,
                "payment_mode_id": self.acquirer_manual.id,
            },
        )
        # Still open because the manual payment doesn't validate the invoice
        transaction = self.invoice.transaction_ids
        self.assertEqual(len(self.invoice.transaction_ids), 1)
        self.assertEqual(transaction.state, "pending")
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.invoice.payment_state, "not_paid")
        self.assertIn(str(self.invoice.name), transaction.reference)
        self.assertEqual(self.acquirer_manual, transaction.acquirer_id)
        self.assertAlmostEqual(
            residual, transaction.amount, places=self.precision
        )

    def test_pay_invoice_with_electronic(self):
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.invoice.payment_state, "not_paid")
        residual = self.invoice.amount_residual
        self.payment_electronic_service.dispatch(
            "add_payment",
            params={
                "target": "invoice",
                "invoice_id": self.invoice.id,
                "payment_mode_id": self.acquirer_electronic.id,
            },
        )
        transaction = self.invoice.transaction_ids
        self.assertEqual(len(self.invoice.transaction_ids), 1)
        self.assertEqual(transaction.state, "done")
        # Simulate Cron
        transaction._post_process_after_done()
        # Still open because the manual payment doesn't validate the invoice
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertIn(str(self.invoice.name), transaction.reference)
        self.assertEqual(self.acquirer_electronic, transaction.acquirer_id)
        self.assertAlmostEqual(
            residual, transaction.amount, places=self.precision
        )

    def test_transactions(self):
        self._set_transaction()

        response = self.service.dispatch(
            "search", params={"id": self.invoice.id}
        )
        transactions = response.get("data")[0].get("transactions")
        transaction = transactions[0]
        self.assertEqual("draft", transaction.get("state"))
