# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models
from odoo.tools import groupby


class AccountPaymentOrder(models.Model):
    _name = "account.payment.order"
    _inherit = [_name, "invader.payable"]

    transaction_ids = fields.Many2many(
        comodel_name="payment.transaction",
        relation="account_payment_order_transaction_rel",
        column1="payment_order_id",
        column2="transaction_id",
        string="Payment transactions",
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

    @api.depends("payment_line_ids")
    def _compute_authorized_transaction_ids(self):
        for rec in self:
            rec.authorized_transaction_ids = rec.transaction_ids.filtered(
                lambda t: t.state == "authorized"
            )

    @api.depends("payment_line_ids")
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

    def action_uploaded_cancel(self):
        self._remove_related_draft_transaction()
        return super().action_uploaded_cancel()

    def _remove_related_draft_transaction(self):
        if not all(
            t.state in ("draft", "cancel", "error")
            for t in self.transaction_ids
        ):
            raise exceptions.UserError(
                _("Some transaction are already validated.")
            )
        return self.transaction_ids.unlink()

    def generate_payment_file(self):
        """
        Inherit to avoid file generation for SEPA payment
        """
        if (
            self.payment_method_id.code == "sepa_direct_debit"
            and self.payment_type == "inbound"
            and self.payment_method_id.payment_acquirer_id.provider == "adyen"
        ):
            return False, False
        return super().generate_payment_file()

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        self.ensure_one()
        list_vals = []
        if self.batch_booking:
            for _key, list_lines in groupby(
                self.payment_line_ids,
                key=lambda l: l.partner_bank_id,
            ):
                # Work on a recordset instead of a list of records
                lines = self.payment_line_ids.browse(
                    [li.id for li in list_lines]
                )
                list_vals.append(
                    lines._invader_prepare_payment_transaction_data(
                        acquirer_id
                    )
                )
        else:
            list_vals = [
                line._invader_prepare_payment_transaction_data(acquirer_id)
                for line in self.payment_line_ids
            ]
        return list_vals

    @api.model
    def _cron_create_transaction(self):
        """ """
        payment_orders = self.search(
            [
                ("state", "=", "open"),
                ("payment_mode_id.payment_type", "=", "inbound"),
                ("payment_method_id.code", "=", "sepa_direct_debit"),
            ]
        )
        # Sepa is compute not stored so filter manually
        # + filter only to adyen
        for payment_order in payment_orders.filtered(
            lambda p: p.sepa
            and p.payment_method_id.payment_acquirer_id.provider == "adyen"
        ):
            payment_order._generate_transaction_adyen()
            payment_order.open2generated()
            payment_order.generated2uploaded()

    def _generate_transaction_adyen(self):
        transaction_data = self._invader_prepare_payment_transaction_data(
            self.payment_method_id.payment_acquirer_id
        )
        return self.env["payment.transaction"].create(transaction_data)
