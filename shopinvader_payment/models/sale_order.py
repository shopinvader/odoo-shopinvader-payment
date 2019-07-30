# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "invader.payable"]

    @api.multi
    def _get_transaction_to_capture_amount(self):
        """
        Get the amount to capture of the transaction
        :return: float
        """
        return self.amount_total

    def _prepare_payment_transaction_data(self, payment_mode):
        """
        This returns the dict with all data for transaction from sale order
        :param payment_mode:
        :return: dict
        """
        self.ensure_one()
        # TODO is there no self.currency_id?
        currency = self.pricelist_id.currency_id
        partner = self.partner_id
        vals = {
            "amount": self._get_transaction_to_capture_amount(),
            "currency_id": currency.id,
            "partner_id": partner.id,
            "payment_mode_id": payment_mode.id,
        }
        return vals
