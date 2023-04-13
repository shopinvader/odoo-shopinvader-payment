# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_data = fields.Char(groups="base.group_user")

    def _prepare_adyen_payments_request(self, payment_method):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment
        Prepare payments request
        :param payment_method:
        :return:
        """
        request = super()._prepare_adyen_payments_request(
            payment_method=payment_method
        )
        if "klarna" in payment_method.get("type", ""):
            payables = self._get_invader_payables()
            request.update(
                payables._prepare_adyen_payment_klarna(self, payment_method)
            )
        return request
