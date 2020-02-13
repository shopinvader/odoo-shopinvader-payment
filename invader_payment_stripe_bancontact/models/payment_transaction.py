# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools.float_utils import float_round


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    @api.multi
    def _charge_get_formatted_amount(self):
        """
        Transform the amount to correspond to the acquirer provider
        :return: type needed by the acquirer provider (float/int)
        """
        self.ensure_one
        if self.acquirer_id.provider == "stripe_bancontact":
            return int(float_round(self.amount * 100, 2))
        return super()._charge_get_formatted_amount()
