# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import Component
from odoo.addons.shopinvader import shopinvader_response


class SaleOrderPaymentTransactionEventListener(Component):
    _name = "sale.order.payment.transaction.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["sale.order"]

    def _confirm_and_invalidate_session(self, sale_order):
        shopinvader_backend = sale_order.shopinvader_backend_id
        if not shopinvader_backend:
            return
        sale_order.action_confirm_cart()
        response = shopinvader_response.get()
        response.set_session("cart_id", 0)
        response.set_store_cache("cart", {})
        # TODO we should not have to return the last_sale information into the
        # response, only the id...
        # This code is an awful hack... We should never have to call
        # a service implementation from here. That should be the responsibility
        # of the client to request the cart info to store into ist cache once
        # once the cache is reset
        collection = _PseudoCollection("shopinvader.backend", self.env)
        work = self.work.work_on(collection=collection)
        work.shopinvader_backend = shopinvader_backend
        res = work.component(usage="cart")._to_json(sale_order)
        response.set_store_cache("last_sale", res.get("data", {}))
        # end of awful code ....

    def on_payment_transaction_done(self, sale_order, transaction):
        self._confirm_and_invalidate_session(sale_order)

    def on_payment_transaction_authorized(self, sale_order, transaction):
        self._confirm_and_invalidate_session(sale_order)
