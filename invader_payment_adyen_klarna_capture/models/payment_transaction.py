# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    def _set_transaction_done(self):
        """
        Inherit because in Adyen Klarna payment method,
        the payment is set as authorized and is not really captured.
        The capture is done later (manually or not).
        """
        adyen_klarna_trx = self.filtered(
            lambda tr: "klarna" in (tr.adyen_payment_method or "")
            and tr.state == "draft"
        )
        others_trx = self - adyen_klarna_trx
        result = None
        if adyen_klarna_trx:
            result = adyen_klarna_trx._set_transaction_authorized()
        if others_trx:
            result = super(
                PaymentTransaction, others_trx
            )._set_transaction_done()
        return result
