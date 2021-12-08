# -*- coding: utf-8 -*-
# Copyright 2020 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.addons.component.core import WorkContext


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.multi
    def capture_one_transaction(self):
        super(PaymentTransaction, self).capture_one_transaction()
        if self.acquirer_id.provider == "stripe":
            work = WorkContext(
                model_name="shopinvader.backend",
                collection=self.sale_order_ids.mapped(
                    "shopinvader_backend_id"
                ),
            )
            stripe_service = work.component(usage="payment_stripe")
            stripe_service.capture_payment(
                "transaction_orders",
                stripe_payment_intent_id=self.acquirer_reference,
            )
