# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from odoo.addons.shopinvader_api_cart.routers.cart import CartHelper, cart_helper
from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.schemas import PaymentData

cart_payment_router = APIRouter(tags=["carts"])


@cart_payment_router.get("/{uuid}/payable")
@cart_payment_router.get("/current/payable")
def init(
    helper: Annotated[CartHelper, Depends(cart_helper)],
    uuid: UUID | None = None,
) -> PaymentData:
    """Prepare payment data for the current cart.

    This route is authenticated, so we can verify the cart
    is accessible by the authenticated partner.
    """
    cart = helper._get_cart(uuid)
    if not cart:
        raise HTTPException(status_code=404)
    sale_order = helper.env["sale.order"].browse(cart.id)
    payment_data = {
        "payable": Payable(
            payable_id=cart.id,
            payable_model="sale.order",
            payable_reference=sale_order.name,
            amount=sale_order.amount_total,
            currency_id=sale_order.currency_id.id,
            partner_id=sale_order.partner_id.id,
            company_id=sale_order.company_id.id,
        ).encode(helper.env),
        "payable_reference": sale_order.name,
        "amount": sale_order.amount_total,
        "currency_code": sale_order.currency_id.name,
        "amount_formatted": sale_order.currency_id.format(sale_order.amount_total),
    }
    return PaymentData(**payment_data)
