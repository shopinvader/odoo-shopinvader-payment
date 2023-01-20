# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class PaymentServiceAdyen(AbstractComponent):
    _inherit = "payment.service.adyen"

    def _prepare_adyen_payments_request(self, transaction, payment_method):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment
        Prepare payments request
        :param transaction:
        :param payment_method:
        :return:
        """
        request = super()._prepare_adyen_payments_request(
            transaction=transaction, payment_method=payment_method
        )
        if "klarna" in payment_method.get("type", ""):
            payables = transaction._get_invader_payables()
            request.update(
                payables._prepare_adyen_payment_klarna(
                    transaction, payment_method
                )
            )
        return request
