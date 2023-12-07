# Copyright 2024 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from werkzeug.urls import url_join

from odoo import fields, models

PAYMENT_BASE_URL_KEY = "payment_base_url"


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    return_url_suffix = fields.Char()

    def _get_filled_url_suffix(self, base_url=False):
        self.ensure_one()
        base_url = base_url or self.env.context.get(PAYMENT_BASE_URL_KEY)
        if not base_url or not self.return_url_suffix:
            return ""
        return url_join(base_url, self.return_url_suffix)
