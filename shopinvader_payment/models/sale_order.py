# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "shopinvader.payable"]

    def _get_target_provider(self):
        """

        :param target: payment recordset
        :return: str
        """
        return self.payment_mode_id.provider

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
        currency = self.pricelist_id.currency_id
        partner = self.partner_id
        vals = {
            "amount": self._get_transaction_to_capture_amount(),
            "currency_id": currency.id,
            "partner_id": partner.id,
            "sale_order_ids": [(6, 0, self.ids)],
        }
        vals.update(self._get_shopinvader_payment_mode(payment_mode))
        return vals

    def _attach_transaction(self, payment_transaction):
        """
        Attach the transaction to sale order
        :param payment_transaction:
        :return: bool
        """
        self.ensure_one()
        self.transaction_ids |= payment_transaction
        return True
