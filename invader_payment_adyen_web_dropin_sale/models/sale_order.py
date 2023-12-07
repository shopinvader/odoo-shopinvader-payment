# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.invader_payment_adyen_web_dropin.models.payment_acquirer import (
    ADYEN_PROVIDER,
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_payment_line(self, transaction, line):
        values = super()._prepare_payment_line(transaction, line)
        if transaction.acquirer_id.provider == ADYEN_PROVIDER:
            values.update(self._prepare_payment_line_dropin(transaction, line))
        return values

    def _prepare_payment_line_dropin(self, transaction, line):
        values = {
            "quantity": line.product_uom_qty,
            "taxPercentage": self._get_formatted_amount(
                transaction, line.tax_id.amount
            ),
            "amountIncludingTax": self._get_formatted_amount(
                transaction, line.price_unit
            ),
        }
        return values
