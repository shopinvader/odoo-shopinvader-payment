# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res["authorize"].append("adyen")
        return res
