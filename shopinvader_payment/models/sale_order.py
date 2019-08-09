# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class SaleOrder(models.Model):

    _name = "sale.order"
    _inherit = ["sale.order", "invader.payable"]

    def _invader_get_available_payment_methods(self):
        self.ensure_one()
        return self.shopinvader_backend_id.payment_method_ids

    def _invader_prepare_payment_transaction_data(self, payment_mode):
        self.ensure_one()
        vals = {
            "amount": self.amount_total,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "acquirer_id": payment_mode.payment_acquirer_id.id,
            "sale_order_ids": [(6, 0, self.ids)],
        }
        return vals

    def _invader_payment_start(self, transaction, payment_mode_id):
        self.ensure_one()
        vals = {"payment_mode_id": payment_mode_id.id}
        newvals = self.play_onchanges(vals, ["payment_mode_id"])
        vals.update(newvals)
        self.write(vals)

    def _invader_payment_success(self, transaction):
        res = self.action_confirm_cart()
        return res
