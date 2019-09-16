# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class CartService(Component):
    _name = "shopinvader.cart.service"
    _inherit = [_name, "payment.service.adyen"]

    def _execute_payment_action(
        self, provider_name, transaction, target, params
    ):
        """
        Inherit to merge the result of the payment with the current cart
        :param provider_name: str
        :param transaction: transaction recordset
        :param target: recordset
        :param params: dict
        :return: dict
        """
        values = super(CartService, self)._execute_payment_action(
            provider_name, transaction, target, params
        )
        if provider_name == "adyen" and transaction.url:
            cart = target
            result = self._to_json(cart)
            payment = result.setdefault("data", {}).setdefault("payment", {})
            super_payment = values.get("data", {}).get("payment", {})
            if super_payment:
                payment.update(super_payment)
            return result
        return values
