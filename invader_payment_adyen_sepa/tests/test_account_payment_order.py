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
