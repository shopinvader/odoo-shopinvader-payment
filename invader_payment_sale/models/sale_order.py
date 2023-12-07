# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = [_name, "invader.payable"]

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        self.ensure_one()
        vals = super()._invader_prepare_payment_transaction_data(acquirer_id)
        vals.update(
            {
                "sale_order_ids": [(6, 0, self.ids)],
            }
        )
        return vals

    def _get_transaction_amount(self):
        return self.amount_total

    def _get_internal_ref(self):
        return self.name

    def _invader_get_transactions(self):
        return self.transaction_ids

    def _get_shopper_partner(self):
        return self.partner_id

    def _get_billing_partner(self):
        return self.partner_invoice_id or super()._get_billing_partner()

    def _get_delivery_partner(self):
        return self.partner_shipping_id or self._get_delivery_partner()

    def _get_payable_lines(self):
        """
        Return payable lines
        """
        return self.order_line
