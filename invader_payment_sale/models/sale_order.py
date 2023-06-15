# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "invader.payable"]

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        self.ensure_one()
        vals = {
            "amount": self.amount_total,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "acquirer_id": acquirer_id.id,
            "sale_order_ids": [(6, 0, self.ids)],
        }
        return vals

    def _invader_get_transactions(self):
        return self.transaction_ids

    def _get_payable_lines(self):
        """
        Return payable lines
        """
        return self.order_line
