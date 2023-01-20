# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools.float_utils import float_round

from odoo.addons.payment_stripe.models.payment import INT_CURRENCIES


class InvaderPayable(models.AbstractModel):

    _inherit = "invader.payable"

    def _get_formatted_amount(self, transaction, amount):
        """
        The expected amount format by Adyen
        :param transaction: payment.transaction
        :param amount: float
        :return: int
        """
        if transaction.acquirer_id.provider == "stripe":
            currency = transaction.currency_id
            dp_name = transaction.acquirer_id.provider.capitalize()
            digits = self.env["decimal.precision"].precision_get(dp_name)
            res = int(
                amount
                if currency.name in INT_CURRENCIES
                else float_round(amount * 100, digits)
            )
            return res
        return super()._get_formatted_amount(transaction, amount)
