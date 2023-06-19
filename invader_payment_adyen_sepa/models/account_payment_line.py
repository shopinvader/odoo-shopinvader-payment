# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models

from .payment_transaction import ADYEN_SEPA_PAYMENT_METHOD


class AccountPaymentLine(models.Model):
    _name = "account.payment.line"
    _inherit = [_name, "invader.payable"]

    transaction_ids = fields.Many2many(
        comodel_name="payment.transaction",
        relation="account_payment_line_transaction_rel",
        column1="payment_order_line_id",
        column2="transaction_id",
        string="Transactions",
        copy=False,
        readonly=True,
    )
    payment_transaction_count = fields.Integer(
        string="Number of payment transactions",
        compute="_compute_payment_transaction_count",
    )
    authorized_transaction_ids = fields.Many2many(
        "payment.transaction",
        compute="_compute_authorized_transaction_ids",
        string="Authorized Transactions",
        copy=False,
        readonly=True,
    )

    def _get_shopper_partner(self):
        return self.partner_id

    @api.depends("transaction_ids")
    def _compute_authorized_transaction_ids(self):
        for rec in self:
            rec.authorized_transaction_ids = rec.transaction_ids.filtered(
                lambda t: t.state == "authorized"
            )

    def _get_internal_ref(self):
        return self.communication

    @api.depends("transaction_ids")
    def _compute_payment_transaction_count(self):
        """
        Compute function for the field payment_transaction_count.
        Count the number of transaction.
        :return:
        """
        for rec in self:
            rec.payment_transaction_count = len(rec.transaction_ids)

    def action_view_transaction(self):
        """
        Action to view related transactions
        :return: action (dict)
        """
        action = {
            "type": "ir.actions.act_window",
            "name": "Payment Transactions",
            "res_model": "payment.transaction",
        }
        if self.payment_transaction_count == 1:
            action.update(
                {"res_id": self.transaction_ids.id, "view_mode": "form"}
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", self.transaction_ids.ids)],
                }
            )
        return action

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        """
        Self could be a multi-record set.
        We suppose it's already grouped by currency_id and partner_id.
        """
        line = fields.first(self)
        vals = {
            "amount": sum(self.mapped("amount_currency")),
            "currency_id": line.currency_id.id,
            "partner_id": line.partner_id.id,
            "acquirer_id": acquirer_id.id,
            "payment_order_line_ids": [(6, 0, self.ids)],
            "payment_order_ids": [(6, 0, self.mapped("order_id").ids)],
            "reference": " ".join(r._get_internal_ref() for r in self),
            "adyen_payment_method": ADYEN_SEPA_PAYMENT_METHOD,
        }
        return vals
