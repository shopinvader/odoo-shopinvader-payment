# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class InvaderPaymentService(Component):

    _inherit = "invader.payment.service"

    def _invader_find_payable(self, target, **params):
        """
        Check if target == "current_cart" then returns the cart from session
        :param params:
        :return:
        """
        if target == "current_cart":
            return self.component(usage="cart")._get()
        return super()._invader_find_payable(target, **params)

    def _invader_get_target_validator(self):
        """
        # returns a list of strings
        # used to add in the validator
        :return:
        """
        res = super()._invader_get_target_validator()
        target = res.get("target")
        allowed = target.get("allowed", [])
        allowed.append("current_cart")
        target.update({"allowed": allowed})
        return res
