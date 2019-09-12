# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServiceStripe(Component):
    _name = "test.invader.payment.service"
    _inherit = "invader.payment.service"
    _collection = "res.partner"

    def _invader_find_payable_from_target(self, target, **params):
        if target == "demo_partner":
            return self.env.ref("base.res_partner_1")
        raise NotImplementedError

    def _invader_get_target_validator(self):
        res = super(PaymentServiceStripe, self)._invader_get_target_validator()
        res["target"]["allowed"].append("demo_partner")
        return res
