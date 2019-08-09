# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# TO REMOVE IN V12...  provided by sale addon

from openerp import api, fields, models


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    sale_order_ids = fields.Many2many(
        "sale.order",
        "sale_order_transaction_rel",
        "transaction_id",
        "sale_order_id",
        string="Sales Orders",
        copy=False,
        readonly=True,
    )

    sale_order_ids_nbr = fields.Integer(
        compute="_compute_sale_order_ids_nbr", string="# of Sales Orders"
    )

    @api.depends("sale_order_ids")
    def _compute_sale_order_ids_nbr(self):
        for trans in self:
            trans.sale_order_ids_nbr = len(trans.sale_order_ids)

    @api.model
    def _compute_reference_prefix(self, values):
        prefix = super(PaymentTransaction, self)._compute_reference_prefix(
            values
        )
        if not prefix and values and values.get("sale_order_ids"):
            many_list = self.resolve_2many_commands(
                "sale_order_ids", values["sale_order_ids"], fields=["name"]
            )
            return ",".join(dic["name"] for dic in many_list)
        return prefix

    @api.multi
    def _log_payment_transaction_sent(self):
        super(PaymentTransaction, self)._log_payment_transaction_sent()
        for trans in self:
            post_message = trans._get_payment_transaction_sent_message()
            for so in trans.sale_order_ids:
                so.message_post(body=post_message)

    @api.multi
    def _log_payment_transaction_received(self):
        super(PaymentTransaction, self)._log_payment_transaction_received()
        for trans in self.filtered(
            lambda t: t.provider not in ("manual", "transfer")
        ):
            post_message = trans._get_payment_transaction_received_message()
            for so in trans.sale_order_ids:
                so.message_post(body=post_message)

    @api.model
    def create(self, vals):
        if not vals.get("reference"):
            vals["reference"] = self._compute_reference(values=vals)
        return super(PaymentTransaction, self).create(vals)
