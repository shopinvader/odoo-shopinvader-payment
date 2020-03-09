# Copyright 2020 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.component.core import WorkContext


class AcquirerStripe(models.Model):
    _inherit = "payment.acquirer"

    def _get_feature_support(self):
        """Get advanced feature support by provider.
        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerStripe, self)._get_feature_support()
        res["authorize"].append("stripe")
        return res


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def stripe_s2s_capture_transaction(self, **kwargs):
        work = WorkContext(
            model_name="shopinvader.backend",
            collection=self.sale_order_ids.mapped("shopinvader_backend_id"),
        )
        stripe_service = work.component(usage="payment_stripe")
        stripe_service.capture_payment(
            "transaction_orders",
            stripe_payment_intent_id=self.acquirer_reference,
        )

    def stripe_s2s_void_transaction(self, **kwargs):
        return
