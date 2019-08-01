# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class InvaderPaymentService(Component):

    _inherit = "invader.payment.service"

    def _invader_find_payable(self, target, **params):
        if target == "current_cart":
            return self.component(usage="cart")._get()
        return super()._invader_find_payable(target, **params)

    def _invader_get_target_validator(self):
        res = super()._invader_get_target_validator()
        res["target"]["allowed"].append("current_cart")
        return res

    def _invader_get_payment_sucess_reponse_data(self, target, **params):
        res = super()._invader_get_payment_sucess_reponse_data(target, **params)
        if target == "current_cart":
            cart_service = self.component(usage="cart")
            cart = cart_service._get()
            res = cart_service._to_json(cart)
            res.update({
                "store_cache": {"last_sale": res["data"], "cart": {}},
                "set_session": {"cart_id": 0},
            })
        return res
