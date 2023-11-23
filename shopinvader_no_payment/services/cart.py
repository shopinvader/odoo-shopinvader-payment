# Copyright 2022 Akretion (http://www.akretion.com)
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class CartService(Component):
    _inherit = "shopinvader.cart.service"

    def confirm_sale(self, **params):
        cart = self._get()
        cart.action_confirm_cart()
        res = self._to_json(cart)
        # inspired from shopinvader_quotation/services/cart.py
        res.update(
            {
                "store_cache": {"last_sale": res["data"], "cart": {}},
                "set_session": {"cart_id": 0},
            }
        )
        return res

    # Validator

    def _validator_confirm_sale(self):
        return {}
