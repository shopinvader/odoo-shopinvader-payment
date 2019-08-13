# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = "sale.order"

    transaction_ids = fields.Many2many(
        "payment.transaction",
        "sale_order_transaction_rel",
        "sale_order_id",
        "transaction_id",
        string="Transactions",
        copy=False,
        readonly=True,
    )
    authorized_transaction_ids = fields.Many2many(
        "payment.transaction",
        compute="_compute_authorized_transaction_ids",
        string="Authorized Transactions",
        copy=False,
        readonly=True,
    )
    payment_transaction_count = fields.Integer(
        string="Number of payment transactions",
        compute="_compute_payment_transaction_count",
    )

    @api.depends("transaction_ids")
    def _compute_authorized_transaction_ids(self):
        for rec in self:
            rec.authorized_transaction_ids = rec.transaction_ids.filtered(
                lambda t: t.state == "authorized"
            )

    @api.depends("transaction_ids")
    def _compute_payment_transaction_count(self):
        for rec in self:
            rec.payment_transaction_count = len(rec.transaction_ids)

    @api.multi
    def action_view_transaction(self):
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
