# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from typing import Annotated, Any
from urllib.parse import urljoin

from fastapi import Depends, Form
from fastapi.responses import RedirectResponse

from odoo.addons.payment.models.payment_transaction import PaymentTransaction
from odoo.addons.shopinvader_api_payment.routers import payment_router
from odoo.addons.shopinvader_api_payment.routers.payment import payment_helper
from odoo.addons.shopinvader_api_payment.routers.utils import (
    add_query_params_in_url,
    tx_state_to_redirect_status,
)
from odoo.addons.shopinvader_api_payment.schemas import TransactionProcessingValues
from odoo.addons.shopinvader_router_helper import VirtualModel

_logger = logging.getLogger(__name__)


class PaymentHelper(VirtualModel):
    _inherit = "shopinvader_api_payment.payment_router.helper"

    def _update_payable_with_transaction(
        self,
        payable: str,
        tx_sudo: PaymentTransaction,
    ) -> str:
        payable_obj = self._decode_payable(payable)
        payable_obj.transaction_id = tx_sudo.id
        return payable_obj.encode(self.env)

    def _get_custom_redirect_form_html(
        self,
        tx_sudo: PaymentTransaction,
        payable: Annotated[str, Form()],
        frontend_redirect_url: Annotated[str, Form()],
    ) -> str:
        shopinvader_api_payment_base_url = tx_sudo.env.context.get(
            "shopinvader_api_payment_base_url", ""
        )
        payable_with_transaction = self._update_payable_with_transaction(
            payable, tx_sudo
        )
        redirect_url = urljoin(shopinvader_api_payment_base_url, "custom/pending")

        if not frontend_redirect_url:
            frontend_redirect_url = tx_sudo.shopinvader_frontend_redirect_url or ""

        return f"""\n
        <form method=\"POST\"
        action=\"{redirect_url}\">\n
                    <input type=\"hidden\" name=\"payable\"
                    value=\"{payable_with_transaction}\"/>\n
                    <input type=\"hidden\" name=\"frontend_redirect_url\"
                    value=\"{frontend_redirect_url}\"/>\n
                          </form>"""

    def _get_tx_processing_values(
        self, tx_sudo: PaymentTransaction, **kwargs: Any
    ) -> TransactionProcessingValues:
        tx_processing_values = super()._get_tx_processing_values(tx_sudo, **kwargs)
        if tx_sudo.provider_id.code == "custom":
            tx_processing_values.redirect_form_html = (
                self._get_custom_redirect_form_html(
                    tx_sudo,
                    kwargs.get("payable", ""),
                    kwargs.get("frontend_redirect_url", ""),
                )
            )
        return tx_processing_values


@payment_router.post("/payment/providers/custom/pending")
def custom_payment_pending_msg(
    payable: Annotated[str, Form()],
    frontend_redirect_url: Annotated[str, Form()],
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
):
    payable_obj = helper._decode_payable(payable)
    tx_sudo = (
        helper.env["payment.transaction"].sudo().browse(payable_obj.transaction_id)
    )
    tx_sudo._set_pending()
    return RedirectResponse(
        url=add_query_params_in_url(
            frontend_redirect_url,
            {
                "status": tx_state_to_redirect_status(tx_sudo.state),
                "pending_message": tx_sudo.provider_id.pending_msg,
            },
        ),
        status_code=303,
    )
