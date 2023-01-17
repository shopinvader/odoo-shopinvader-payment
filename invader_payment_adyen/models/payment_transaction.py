# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_data = fields.Char(groups="base.group_user")
    adyen_payment_method = fields.Char()

    def _get_platform(self):
        """
        For Adyen: return 'test' or 'live' depending on acquirer value
        :return: str
        """
        if self.acquirer_id.provider == "adyen":
            state = self.acquirer_id.state
            return "test" if state in ("disabled", "test") else "live"
        return super()._get_platform()
