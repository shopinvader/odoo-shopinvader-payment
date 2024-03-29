# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import request

from odoo.addons.component.core import Component
from odoo.addons.shopinvader import shopinvader_response


class AccountMovePaymentTransactionEventListener(Component):
    _name = "account.move.payment.transaction.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def _confirm_and_invalidate_session(self, account_invoice):
        if not account_invoice.shopinvader_backend_id:
            return
        # In case of the invoice is not already validated
        if account_invoice.state != "posted":
            account_invoice.action_post()
        try:
            sess_cart_id = request.httprequest.environ.get("HTTP_SESS_CART_ID")
        except RuntimeError:
            # not in an http request (testing?)
            sess_cart_id = None
        response = shopinvader_response.get(raise_if_not_found=False)
        if response and sess_cart_id:
            response.set_session("invoice_id", 0)
            response.set_store_cache("invoice", {})
            response.set_store_cache("last_invoice_id", account_invoice.id)

    def on_payment_transaction_done(self, account_invoice, transaction):
        self._confirm_and_invalidate_session(account_invoice)

    def on_payment_transaction_authorized(self, account_invoice, transaction):
        self._confirm_and_invalidate_session(account_invoice)

    def on_payment_transaction_pending(self, account_invoice, transaction):
        if transaction.acquirer_id.provider == "transfer":
            self._confirm_and_invalidate_session(account_invoice)
