# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    def _get_invader_payables(self):
        self.ensure_one()
        if self.sale_order_ids:
            return self.sale_order_ids
        return super(PaymentTransaction, self)._get_invader_payables()

    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        for order in self.sale_order_ids.filtered(
            lambda so: so.state in ("draft", "sent")
        ):
            transactions = order.transaction_ids
            done_transactions = transactions.filtered(lambda t: t.state == "done")
            paid_amount = sum(done_transactions.mapped("amount"))
            if order.currency_id.compare_amounts(order.amount_total, paid_amount) == 0:
                order.with_context(send_email=True).action_confirm()
                unfinished_transactions = transactions - done_transactions
                unfinished_transactions._set_transaction_cancel()
        return super()._check_amount_and_confirm_order()
