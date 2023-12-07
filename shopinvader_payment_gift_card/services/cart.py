# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.shopinvader_gift_card.services.gift_card import (
    JSONIFY_GIFT_CARD,
    JSONIFY_GIFT_CARD_LINE,
)


def to_date(value):
    return date.fromisoformat(value)


class GiftCardCodeInput(Datamodel):
    _name = "gift.card.code.input"
    code = fields.String()


class GiftCardAmountInput(Datamodel):
    _name = "gift.card.amount.input"
    card = fields.Integer()
    code = fields.String()
    gift_card_amount = fields.Float()


class GiftCardLineInput(Datamodel):
    _name = "gift.card.line.input"
    line_id = fields.Integer()


class CartService(Component):
    _inherit = "shopinvader.cart.service"

    @restapi.method(
        routes=[(["/get_gift_card_from_code"], "GET")],
        input_param=restapi.Datamodel("gift.card.code.input"),
    )
    def get_gift_card_from_code(self, params):
        params = params.dump()
        code = params.get("code", " no_code ")
        gift_card = self.env["gift.card"].search([("code", "=", code)])
        if gift_card:
            self.env["gift.card"].check_gift_card_code(gift_card.code)
            if gift_card.state == "active":
                return gift_card.jsonify(self._parser_giftcard())

    def _parser_giftcard(self):
        return JSONIFY_GIFT_CARD

    def _parser_giftcard_line(self):
        return JSONIFY_GIFT_CARD_LINE

    @restapi.method(
        routes=[(["/gift_card_amount_validation"], "GET")],
        input_param=restapi.Datamodel("gift.card.amount.input"),
    )
    def gift_card_amount_validation(self, params):
        params = params.dump()
        card = params.get("card", False)
        code = params.get("code", False)
        gift_card_amount = params.get("gift_card_amount")
        gift_card = self.env["payment.transaction"]._get_and_check_gift_card(
            card=card, code=code
        )
        gift_card_amount = self._check_gift_card_line_amount(card, gift_card_amount)
        line = self.env["payment.transaction"]._create_gift_card_line(
            amount=gift_card_amount, card=gift_card, code=code
        )
        cart = self._get()
        line.beneficiary_id = cart.partner_id
        cart.write({"gift_card_line_ids": [(4, line.id)]})
        return line.jsonify(self._parser_giftcard_line())

    def _check_gift_card_line_amount(self, card, gift_card_amount):
        gift_card = self.env["gift.card"].browse(card)
        cart = self._get()
        if cart.remain_amount < gift_card_amount and gift_card.is_divisible:
            return cart.remain_amount
        elif not gift_card.is_divisible:
            if cart.remain_amount < gift_card.initial_amount:
                raise UserError(
                    _(
                        "The Gift Card amount is higher than the current"
                        " cart amount, impossible to use the gift card "
                        "in that case."
                    )
                )
            else:
                return gift_card.initial_amount
        else:
            return gift_card_amount

    @restapi.method(
        routes=[(["/unlink_gift_card_line"], "GET")],
        input_param=restapi.Datamodel("gift.card.line.input"),
    )
    def unlink_gift_card_line(self, params):
        params = params.dump()
        line = params.get("line_id")
        cart = self._get()
        cart.write({"gift_card_line_ids": [(2, line)]})
        return self._to_json(cart)

    def _convert_one_sale(self, sale):
        res = super()._convert_one_sale(sale)
        res.update(
            {
                "remain_amount": sale.remain_amount,
                "gift_card_line_ids": self._convert_gift_card_line(
                    sale.gift_card_line_ids
                ),
            }
        )
        return res

    def _parser_gift_card_line(self):
        return ["id", "name", "amount_used", "validation_mode", "beneficiary_id"]

    def _convert_gift_card_line(self, gift_card_lines):
        return {
            "items": gift_card_lines.jsonify(self._parser_gift_card_line()),
            "count": len(gift_card_lines),
        }
