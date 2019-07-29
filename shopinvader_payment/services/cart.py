# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class CartService(Component):

    _inherit = "shopinvader.cart.service"

    def _include_payment(self, target, values):
        """
        Include payment details
        :param target: recordset
        :param values: dict
        :return: dict
        """
        values.update({"payment": target._get_shopinvader_payment_info()})
        return values

    def _convert_one_sale(self, sale):
        """
        Add Payment information into cart
        :return:
        """
        res = super()._convert_one_sale(sale)
        res = self._include_payment(sale, res)
        return res

    def _action_after_payment(self, target):
        """
        Confirm the cart after the payment
        :param target: payment recordset
        :return: dict
        """
        values = {}
        values.update(self._confirm_cart(target))
        return values
