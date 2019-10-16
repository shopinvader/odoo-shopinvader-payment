# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.shopinvader import shopinvader_response


class AccountInvoicePaymentTransactionEventListener(Component):
    _name = "account.invoice.payment.transaction.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.invoice"]

    def _confirm_and_invalidate_session(self, account_invoice):
        shopinvader_backend = account_invoice.shopinvader_backend_id
        if not shopinvader_backend:
            return
        # In case of the invoice is not already validated
        account_invoice.action_invoice_open()
        response = shopinvader_response.get()
        response.set_session("invoice_id", 0)
        response.set_store_cache("invoice", {})
        response.set_store_cache("last_invoice_id", account_invoice.id)

    def on_payment_transaction_done(self, account_invoice, transaction):
        self._confirm_and_invalidate_session(account_invoice)

    def on_payment_transaction_pending(self, account_invoice, transaction):
        if transaction.acquirer_id.provider == "transfer":
            self._confirm_and_invalidate_session(account_invoice)
