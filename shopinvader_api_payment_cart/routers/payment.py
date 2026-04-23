# Copyright Odoo SA (https://odoo.com)
# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.fields import Command

from odoo.addons.shopinvader_api_payment.routers.utils import Payable
from odoo.addons.shopinvader_api_payment.schemas import TransactionCreate
from odoo.addons.shopinvader_router_helper import VirtualModel


class PaymentHelper(VirtualModel):
    _inherit = "shopinvader_api_payment.payment_router.helper"

    def _get_additional_transaction_create_values(
        self,
        data: TransactionCreate,
        payable_obj: Payable,
    ) -> dict:
        additional_transaction_create_values = (
            super()._get_additional_transaction_create_values(data, payable_obj)
        )
        if payable_obj.payable_model == "sale.order":
            additional_transaction_create_values.update(
                {
                    "sale_order_ids": [Command.set([payable_obj.payable_id])],
                }
            )
        return additional_transaction_create_values
