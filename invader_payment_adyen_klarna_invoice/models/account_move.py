# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.fields import first


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_shopper(self):
        return self.partner_id

    def _get_klarna_delivery(self):
        return self.partner_shipping_id or super()._get_klarna_delivery()

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
                "taxPercentage": transaction._get_formatted_amount(
                    force_amount=first(line.tax_ids).amount
                ),
                "amountIncludingTax": transaction._get_formatted_amount(
                    force_amount=line.price_unit
                ),
            }
        )
        return values
