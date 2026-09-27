# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.schemas import PaymentData
from odoo.addons.shopinvader_api_quotation.routers.quotation import (
    QuotationHelper,
    quotation_helper,
)
from odoo.addons.shopinvader_schema_sale.schemas.sale import Sale

quotation_payment_router = APIRouter(tags=["quotations"])


@quotation_payment_router.get("/quotations/{quotation_id}/payable")
def init(
    helper: Annotated[QuotationHelper, Depends(quotation_helper)],
    quotation_id: int,
) -> PaymentData:
    """Prepare payment data for the current quotation.

    This route is authenticated, so we can verify the quotation
    is accessible by the authenticated partner.
    """
    quotation = Sale.from_sale_order(helper.get(quotation_id))
    if not quotation:
        raise HTTPException(status_code=404)
    sale_order = helper.env["sale.order"].browse(quotation.id)
    payment_data = {
        "payable": Payable(
            payable_id=quotation.id,
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
