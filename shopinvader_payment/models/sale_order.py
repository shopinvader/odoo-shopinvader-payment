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

    def _invader_prepare_payment_transaction_data(self, payment_mode):
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
            "acquirer_id": payment_mode.payment_acquirer_id.id,
            "sale_order_ids": [(6, 0, self.ids)],
        }
        return vals

    def _invader_get_available_payment_methods(self):
        """
        Return all payment modes available for the sale order with
        its shopinvader backend
        :return:
        """
        return self.shopinvader_backend_id.payment_method_ids

    def _get_shopinvader_payment_data(self):
        """
        Specific method to shopinvader to retrieve the payment dict information
        to pass to the front-end
        * Available methods
        * The payment mode
        * The amount
        :return:
        """
        self.ensure_one()
        payment_methods = self._invader_get_available_payment_methods()
        selected_method = payment_methods.filtered(
            lambda m: m.payment_mode_id == self.payment_mode_id
        )
        values = {
            "available_methods": {
                "count": len(payment_methods),
                "items": self._get_payment_method_data(payment_methods),
            },
            "selected_method": self._get_payment_method_data(selected_method),
            "amount": self._get_transaction_to_capture_amount(),
        }
        return values

    def _get_payment_method_data(self, methods):
        res = []
        for method in methods:
            res.append(
                {
                    "id": method.payment_mode_id.id,
                    "name": method.payment_mode_id.name,
                    "provider": method.payment_mode_id.provider,
                    "code": method.code,
                    "description": method.description,
                }
            )
        return res

    def _invader_after_payment(self, transaction):
        res = self.action_confirm_cart()
        return res

    def _invader_payment_start(self, transaction, payment_mode_id):
        self.write({"payment_mode_id": payment_mode_id.id})
