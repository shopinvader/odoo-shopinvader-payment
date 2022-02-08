# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.http import request

from odoo.addons.component.core import Component
from odoo.addons.shopinvader import shopinvader_response
from odoo.addons.shopinvader.utils import work_on_service_with_partner

_logger = logging.getLogger(__name__)


class SaleOrderPaymentTransactionEventListener(Component):
    _name = "sale.order.payment.transaction.event.listener"
    _inherit = "base.event.listener"
    _apply_on = ["sale.order"]

    def _confirm_and_invalidate_session(self, sale_order):
        shopinvader_backend = sale_order.shopinvader_backend_id
        if not shopinvader_backend:
            return
        sale_order.action_confirm_cart()
        try:
            sess_cart_id = request.httprequest.environ.get("HTTP_SESS_CART_ID")
        except RuntimeError:
            # not in an http request (testing?)
            sess_cart_id = None
        response = shopinvader_response.get(raise_if_not_found=False)
        if response and sess_cart_id:
            response.set_session("cart_id", 0)
            response.set_store_cache("cart", {})
            # TODO we should not have to return the last_sale
            # information into the response, only the id...
            # This code is an awful hack... We should never have to call
            # a service implementation from here.
            # That should be the responsibility of the client
            # to request the cart info to be stored in its own cache
            # once the cache is reset.

            invader_partner = sale_order.partner_id._get_invader_partner(
                shopinvader_backend
            )
            if not invader_partner:
                _logger.error(
                    f"Could not find invader_partner for sale order {sale_order.id}"
                )
                return
            if not invader_partner.active:
                _logger.warning(
                    f"Inactive invader_partner found for sale order {sale_order.id}"
                )
            with work_on_service_with_partner(self.env, invader_partner) as work:
                res = work.component(usage="cart")._to_json(sale_order)
                response.set_store_cache("last_sale", res.get("data", {}))

            # end of awful code ....

    def on_payment_transaction_done(self, sale_order, transaction):
        self._confirm_and_invalidate_session(sale_order)
