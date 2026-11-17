# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from urllib.parse import urljoin

from odoo import models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    def _monetico_form_presign_hook(self, values):
        """Insert shopinvader return url in the form values"""
        shopinvader_api_payment = self.env.context.get("shopinvader_api_payment")
        values = super()._monetico_form_presign_hook(values)
        if not shopinvader_api_payment:
            return values

        shopinvader_api_payment_base_url = self.env.context.get(
            "shopinvader_api_payment_base_url"
        )
        values["url_retour_ok"] = values["url_retour_err"] = urljoin(
            shopinvader_api_payment_base_url, "monetico/return"
        )

        return values
