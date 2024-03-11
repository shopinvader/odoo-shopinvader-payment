# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# isort: skip_file
# Need to skip this file because conflict with black
from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)


class SaleOrderPaymentTransactionEventListener(Component):
    _inherit = "sale.order.payment.transaction.event.listener"

    def on_payment_transaction_pending(self, sale_order, transaction):
        if (
            transaction.acquirer_id.provider
            in transaction.acquirer_id._get_adyen_providers()
        ):
            self._confirm_and_invalidate_session(sale_order)

    def on_payment_transaction_done(self, sale_order, transaction):
        if (
            transaction.acquirer_id.provider
            in transaction.acquirer_id._get_adyen_providers()
        ):
            self._confirm_and_invalidate_session(sale_order)
