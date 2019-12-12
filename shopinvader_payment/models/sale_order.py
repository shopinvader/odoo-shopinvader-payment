# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "invader.payable"]

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        allowed_acquirer = self.shopinvader_backend_id.mapped(
            "payment_method_ids.acquirer_id"
        )
        if acquirer_id not in allowed_acquirer:
            raise UserError(
                _("Acquirer %s is not allowed on backend %s")
                % (acquirer_id.name, self.shopinvader_backend_id.name)
            )
        self.ensure_one()
        vals = {
            "amount": self.amount_total,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "acquirer_id": acquirer_id.id,
            "sale_order_ids": [(6, 0, self.ids)],
        }
        return vals
