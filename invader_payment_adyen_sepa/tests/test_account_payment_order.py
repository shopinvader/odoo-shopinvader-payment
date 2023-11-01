# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import TestCommon


class TestAccountPaymentOrder(TestCommon):
    """
    Tests for account.payment.order
    """

    def test_cron_create_transaction(self):
        self.invoice.action_post()
        self.assertEqual("posted", self.invoice.state)
        self.assertTrue(self.payment_order.sepa)
        self._wizard_fill_payment_lines(self.payment_order)
        # Depending on lines, sepa could be False now
        self.assertTrue(self.payment_order.sepa)
        self.assertGreater(len(self.payment_order.payment_line_ids), 0)
        self.payment_order.draft2open()
        self.AccountPaymentOrder._cron_create_transaction()
        # Ensure transactions created seems correct (not batched)
        self.assertEqual(
            len(self.payment_order.payment_line_ids.transaction_ids),
            len(self.payment_order.payment_line_ids),
        )
        self.assertEqual("uploaded", self.payment_order.state)
        for payment_line in self.payment_order.payment_line_ids:
            transaction = payment_line.transaction_ids
            self.assertAlmostEqual(
                transaction.amount, payment_line.amount_currency
            )
            self.assertEqual(transaction.currency_id, payment_line.currency_id)
            self.assertEqual(transaction.partner_id, payment_line.partner_id)
            self.assertEqual(transaction.acquirer_id, self.acquirer)
            self.assertEqual(transaction.reference, payment_line.communication)
            self.assertEqual(
                self.payment_order.payment_mode_id.company_id,
                self.payment_order.company_id,
            )

    def test_cron_create_transaction_multi_company_empty(self):
        # Disable the payment acquirer with current company.
        # So we shouldn't have a transaction
        self.payment_method_sepa.write(
            {
                "payment_acquirer_id": False,
            }
        )
        self.invoice.action_post()
        self.assertEqual("posted", self.invoice.state)
        self.assertTrue(self.payment_order.sepa)
        self._wizard_fill_payment_lines(self.payment_order)
        # Depending on lines, sepa could be False now
        self.assertTrue(self.payment_order.sepa)
        self.assertGreater(len(self.payment_order.payment_line_ids), 0)
        self.payment_order.draft2open()
        self.AccountPaymentOrder._cron_create_transaction()
        # Ensure no transaction and normal workflow still ok
        self.assertFalse(
            self.payment_order.payment_line_ids.transaction_ids,
        )
        self.assertEqual("open", self.payment_order.state)

    def test_cron_create_transaction_multi_company(self):
        # Disable the payment acquirer with current company.
        self.payment_method_sepa.write(
            {
                "payment_acquirer_id": False,
            }
        )
        # But enable it with another company
        other_company = self.company_fr2
        self.payment_order2 = self.payment_order2.with_company(other_company)
        self.payment_method_sepa.with_company(other_company).write(
            {
                "payment_acquirer_id": self.acquirer.id,
            }
        )
        other_invoice = self.invoice2.with_company(other_company)
        self.invoice.action_post()
        other_invoice.action_post()
        self.assertEqual("posted", self.invoice.state)
        self.assertEqual("posted", other_invoice.state)
        self.assertTrue(self.payment_order.sepa)
        self.assertTrue(self.payment_order2.sepa)
        self._wizard_fill_payment_lines(self.payment_order)
        self._wizard_fill_payment_lines(self.payment_order2)
        # Depending on lines, sepa could be False now
        self.assertTrue(self.payment_order.sepa)
        self.assertTrue(self.payment_order2.sepa)
        self.assertGreater(len(self.payment_order.payment_line_ids), 0)
        self.payment_order.draft2open()
        self.payment_order2.draft2open()
        self.AccountPaymentOrder._cron_create_transaction()
        # Ensure no transaction and normal workflow still ok
        self.assertFalse(
            self.payment_order.payment_line_ids.transaction_ids,
        )
        # The flow for this first payment_order stop here as no acquirer set on this company
        self.assertEqual("open", self.payment_order.state)
        # Payment order in second company
        self.assertTrue(self.payment_order2.payment_line_ids)
        self.assertEqual(
            len(self.payment_order2.payment_line_ids.transaction_ids),
            len(self.payment_order2.payment_line_ids),
        )
        self.assertEqual("uploaded", self.payment_order2.state)
        for payment_line in self.payment_order2.payment_line_ids:
            transaction = payment_line.transaction_ids
            self.assertAlmostEqual(
                transaction.amount, payment_line.amount_currency
            )
            self.assertEqual(transaction.currency_id, payment_line.currency_id)
            self.assertEqual(transaction.partner_id, payment_line.partner_id)
            self.assertEqual(transaction.acquirer_id, self.acquirer)
            self.assertEqual(transaction.reference, payment_line.communication)
            self.assertEqual(
                self.payment_order2.payment_mode_id.company_id,
                self.payment_order2.company_id,
            )
