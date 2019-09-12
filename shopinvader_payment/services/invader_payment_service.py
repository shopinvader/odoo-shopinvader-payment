# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class InvaderPaymentService(Component):
    _inherit = "invader.payment.service"
    _name = "shopinvader.payment.service"
    _collection = "shopinvader.backend"

    def _invader_find_payable_from_target(self, target, **params):
        if target == "current_cart":
            return self.component(usage="cart")._get()
        return super()._invader_find_payable_from_target(target, **params)

    def _invader_get_target_validator(self):
        res = super()._invader_get_target_validator()
        res["target"]["allowed"].append("current_cart")
        return res
