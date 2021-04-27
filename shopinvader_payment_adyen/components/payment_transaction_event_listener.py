# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class SaleOrderPaymentTransactionEventListener(Component):
    _inherit = "sale.order.payment.transaction.event.listener"

    def on_payment_transaction_pending(self, sale_order, transaction):
        if transaction.acquirer_id.provider == "adyen":
            self._confirm_and_invalidate_session(sale_order)
