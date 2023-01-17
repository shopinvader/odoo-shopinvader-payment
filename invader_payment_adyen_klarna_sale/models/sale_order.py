# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_klarna_shopper(self):
        return self.partner_id

    def _get_klarna_billing(self):
        return self.partner_invoice_id or self._get_klarna_shopper()

    def _get_klarna_delivery(self):
        return self.partner_shipping_id or self._get_klarna_shopper()

    def _get_klarna_internal_ref(self):
        return self.reference or self.name

    def _prepare_adyen_payment_klarna_line(
        self, transaction, payment_method, line
    ):
        values = super()._prepare_adyen_payment_klarna_line(
            transaction, payment_method, line
        )
        values.update(
            {
                "quantity": line.product_uom_qty,
                "taxPercentage": self._get_formatted_amount(
                    transaction, line.tax_id.amount
                ),
                "amountIncludingTax": self._get_formatted_amount(
                    transaction, line.price_unit
                ),
            }
        )
        return values
