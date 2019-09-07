# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class CartService(Component):

    _inherit = [
        "shopinvader.cart.service",
        "shopinvader.abstract.payable.sale.service",
    ]
    _name = "shopinvader.cart.service"

    def _convert_one_sale(self, sale):
        """
        Add Payment information into cart
        :return:
        """
        values = super()._convert_one_sale(sale)
        values.update({"payment": self._get_shopinvader_payment_data(sale)})
        return values
