# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools.float_utils import float_round


class InvaderPayable(models.AbstractModel):

    _inherit = "invader.payable"

    def _get_formatted_amount(self, transaction, amount):
        """
        The expected amount format by Adyen
        :param transaction: payment.transaction
        :param amount: float
        :return: int
        """
        if transaction.acquirer_id.provider == "adyen":
            dp_name = transaction.acquirer_id.provider.capitalize()
            digits = self.env["decimal.precision"].precision_get(dp_name)
            res = int(float_round(amount, digits) * 100)
            return res
        return super()._get_formatted_amount(transaction, amount)
