# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.shopinvader import shopinvader_response


class RestPartnerPaymentTransactionEventListener(Component):
    _name = "res.partner.payment.transaction.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["res.partner"]

    def _set_response_session(self, res_partner, state):
        response = shopinvader_response.get()
        response.set_session("payment_state", state)
        response.set_session("partner_id", res_partner.id)

    def on_payment_transaction_pending(self, res_partner, transaction):
        self._set_response_session(res_partner, "pending")

    def on_payment_transaction_done(self, res_parnter, transaction):
        self._set_response_session(res_parnter, "done")
