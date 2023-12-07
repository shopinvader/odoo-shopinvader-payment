# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [_name, "invader.payable"]

    transaction_ids = fields.Many2many(
        comodel_name="payment.transaction",
        relation="account_invoice_transaction_rel",
        column1="invoice_id",
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

    @api.depends("transaction_ids")
    def _compute_authorized_transaction_ids(self):
        for rec in self:
            rec.authorized_transaction_ids = rec.transaction_ids.filtered(
                lambda t: t.state == "authorized"
            )

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
        self.ensure_one()
        vals = super()._invader_prepare_payment_transaction_data(acquirer_id)
        vals.update(
            {
                "invoice_ids": [(6, 0, self.ids)],
            }
        )
        return vals

    def _get_internal_ref(self):
        return self.payment_reference or self.name

    def _get_transaction_amount(self):
        return self.amount_residual

    def _get_billing_partner(self):
        return self.partner_id

    def _invader_set_payment_mode(self, payment_mode):
        self.ensure_one()
        vals = {"payment_mode_id": payment_mode.id}
        newvals = self.play_onchanges(vals, vals.keys())
        vals.update(newvals)
        self.write(vals)

    def _invader_get_transactions(self):
        return self.transaction_ids

    def _get_shopper(self):
        return self.partner_id

    def _get_delivery_partner(self):
        return self.partner_shipping_id or super()._get_delivery_partner()

    def _get_payable_lines(self):
        """
        Return payable lines
        """
        return self.invoice_line_ids
