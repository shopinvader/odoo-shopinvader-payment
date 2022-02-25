# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        for order in self.sale_order_ids.filtered(
            lambda so: so.state in ("draft", "sent")
        ):
            if (
                self.amount == order.remain_amount
                and order.amount_total
                == order.remain_amount
                + sum(order.gift_card_line_ids.mapped("amount_used"))
            ):
                order.with_context(send_email=True).action_confirm()
            else:
                return super()._check_amount_and_confirm_order()

    def _post_process_after_done(self):
        res = super()._post_process_after_done()
        if self.sale_order_ids.gift_card_line_ids:
            for gift_card_line in self.sale_order_ids.gift_card_line_ids:
                if not gift_card_line.transaction_id:
                    self._add_gift_card_transaction(
                        amount=gift_card_line.amount_used, line=gift_card_line
                    )
        return res

    def create_gift_card_payment(self, sale):
        gift_card_acquirer = self.env.ref(
            "account_payment_gift_card.payment_acquirer_gift_card"
        )
        for line in sale.gift_card_line_ids:
            vals = {
                "acquirer_id": gift_card_acquirer.id,
                "amount": line.amount_used,
            }
            transaction = sale._create_payment_transaction(vals)
            transaction._create_payment()
            transaction._reconcile_after_transaction_done()
            line.transaction_id = transaction
