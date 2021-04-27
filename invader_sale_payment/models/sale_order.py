# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.payment_mode_id.capture_payment == "order_confirm":
                order.authorized_transaction_ids.action_capture()
        return res

    @api.multi
    def action_capture(self):
        if any(self.mapped(lambda tx: tx.state != "authorized")):
            raise ValidationError(
                _(
                    "Only transactions in the Authorized status"
                    " can be captured."
                )
            )
        for tx in self:
            tx.capture_one_transaction()

    @api.multi
    def capture_one_transaction(self):
        self.ensure_one()
