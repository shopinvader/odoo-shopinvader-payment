# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class GiftCardPaymentInput(Datamodel):
    _name = "gift.card.payment.input"
    cart = fields.Integer(required=True)


class PaymentServiceGiftCard(AbstractComponent):

    _name = "payment.service.gift.card"
    _inherit = "base.rest.service"
    _usage = "payment_gift_card"
    _description = "REST Services for Gift Card payments"


class PaymentServiceGiftCardShopinvader(Component):
    _name = "payment.service.gift.card.shopinvader"
    _inherit = ["base.shopinvader.service", "payment.service.gift.card"]
    _collection = "shopinvader.backend"

    @restapi.method(
        routes=[(["/gift_card_payment"], "POST")],
        input_param=restapi.Datamodel("gift.card.payment.input"),
    )
    def payment_with_gift_card_only(self, params):
        params = params.dump()
        cart_id = params.get("cart", False)
        cart = self.env["sale.order"].browse(cart_id)
        if sum(cart.gift_card_line_ids.mapped("amount_used")) == cart.amount_total:
            self.env["payment.transaction"].create_gift_card_payment(cart)
            return {}
