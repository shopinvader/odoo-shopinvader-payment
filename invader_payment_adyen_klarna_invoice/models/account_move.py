# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.fields import first


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_klarna_shopper(self):
        return self.partner_id

    def _get_klarna_billing(self):
        return self._get_klarna_shopper()

    def _get_klarna_delivery(self):
        return self.partner_shipping_id or self._get_klarna_shopper()

    def _get_klarna_internal_ref(self):
        return self.ref or self.name

    def _prepare_adyen_payment_klarna_line(
        self, transaction, payment_method, line
    ):
        values = super()._prepare_adyen_payment_klarna_line(
            transaction, payment_method, line
        )
        values.update(
            {
                "quantity": line.quantity,
                "taxPercentage": self._get_formatted_amount(
                    transaction, first(line.tax_ids).amount
                ),
                "amountIncludingTax": self._get_formatted_amount(
                    transaction, line.price_unit
                ),
            }
        )
        return values
