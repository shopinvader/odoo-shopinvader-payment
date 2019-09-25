# -*- coding: utf-8 -*-
# Copyright 2016 Akretion (http://www.akretion.com)
# Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.component.core import Component


class CartService(Component):
    _inherit = "shopinvader.cart.service"

    def _get_available_payment_methods(self, cart):
        for line in cart.order_line:
            if line.product_id.only_quotation:
                # If we have a product that required a quotation in the cart
                # (product without public price) we remove all payment
                # method as it's not possible to pay it.
                # Customer must request a quotation for this cart
                return self.env["shopinvader.payment"].browse(False)
        return super(CartService, self)._get_available_payment_methods(cart)
