# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.component.core import Component


class InvaderPaymentService(Component):

    _inherit = "invader.payment.service"

    def _invader_find_payable_from_target(self, target, **params):
        if target == "current_cart":
            return self.component(usage="cart")._get()
        return super(
            InvaderPaymentService, self
        )._invader_find_payable_from_target(target, **params)

    def _invader_find_payable_from_transaction(self, transaction):
        if transaction.sale_order_ids:
            return transaction.sale_order_ids
        return super(
            InvaderPaymentService, self
        )._invader_find_payable_from_transaction(transaction)

    def _invader_get_target_validator(self):
        res = super(
            InvaderPaymentService, self
        )._invader_get_target_validator()
        res["target"]["allowed"].append("current_cart")
        return res

    def _invader_get_payment_success_reponse_data(
        self, payable, target, **params
    ):
        res = super(
            InvaderPaymentService, self
        )._invader_get_payment_success_reponse_data(payable, target, **params)
        if target == "current_cart":
            res = self.component(usage="cart")._to_json(payable)
            res.update(
                {
                    "store_cache": {
                        "last_sale": res.get("data", {}),
                        "cart": {},
                    },
                    "set_session": {"cart_id": 0},
                }
            )
        return res
