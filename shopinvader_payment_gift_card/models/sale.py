# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    gift_card_line_ids = fields.One2many(
        "gift.card.line",
        inverse_name="sale_order_id",
        string="List of Gift Card uses",
        readonly=True,
    )

    remain_amount = fields.Float("Remaining Amount", compute="_compute_remain_amount")

    @api.depends("gift_card_line_ids", "gift_card_line_ids.amount_used", "amount_total")
    def _compute_remain_amount(self):
        for rec in self:
            if rec.gift_card_line_ids:
                gift_card_amount_total = sum(
                    line.amount_used for line in rec.gift_card_line_ids
                )
                rec.remain_amount = rec.amount_total - gift_card_amount_total
            else:
                rec.remain_amount = rec.amount_total

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        vals = super()._invader_prepare_payment_transaction_data(acquirer_id)
        if self.gift_card_line_ids:
            vals["amount"] = self.remain_amount
        return vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    gift_card_id = fields.Many2one("gift.card")
