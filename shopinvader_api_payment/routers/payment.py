# Copyright Odoo SA (https://odoo.com)
# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from typing import Annotated, Any
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Request

from odoo import api

from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.payment.models.payment_provider import PaymentProvider
from odoo.addons.payment.models.payment_transaction import PaymentTransaction
from odoo.addons.shopinvader_router_helper import VirtualModel

from ..schemas import (
    PaymentDataWithMethods,
    TransactionCreate,
    TransactionProcessingValues,
)
from ..schemas import (
    PaymentProvider as PaymentProviderSchema,
)
from .utils import Payable

_logger = logging.getLogger(__name__)

payment_router = APIRouter(tags=["payment"])


class PaymentHelper(VirtualModel):
    _inherit = "shopinvader.router.helper"
    _name = "shopinvader_api_payment.payment_router.helper"
    _description = "ShopInvader API Payment Router Helper"

    def _get_additional_transaction_create_values(
        self,
        data: TransactionCreate,
        payable_obj: Payable,
    ) -> dict:
        # Intended to be extended for invoices, carts...
        additional_transaction_create_values = {}
        return additional_transaction_create_values

    def _get_tx_create_values(
        self,
        data: TransactionCreate,
        provider_sudo: PaymentProvider,
    ) -> dict:
        payable_obj = self._decode_payable(data.payable)
        additional_transaction_create_values = (
            self._get_additional_transaction_create_values(data, payable_obj)
        )

        is_validation = False  # future
        # compute transaction reference from payable reference
        tx_reference = (
            self.env["payment.transaction"]
            .sudo()
            ._compute_reference(
                provider_code=provider_sudo.code,
                prefix=payable_obj.payable_reference,
                # TODO are custom_create_values and kwargs really needed
                # **(custom_create_values or {}),
                # **kwargs
            )
        )

        return {
            "provider_id": data.provider_id,
            "payment_method_id": data.payment_method_id,
            "reference": tx_reference,
            "amount": payable_obj.amount,
            "currency_id": payable_obj.currency_id,
            "partner_id": payable_obj.partner_id,
            "shopinvader_frontend_redirect_url": data.frontend_redirect_url,
            # 'token_id': token_id,
            "operation": f"online_{data.flow}" if not is_validation else "validation",
            "tokenize": False,
            **additional_transaction_create_values,
        }

    def _get_tx_from_notification_data(
        self, provider: str, data: dict
    ) -> PaymentTransaction:
        return (
            self.env["payment.transaction"]
            .sudo()
            ._get_tx_from_notification_data(provider, data)
        )

    def _create_transaction(
        self,
        data: TransactionCreate,
        provider_sudo: PaymentProvider,
        request: Request,
    ) -> dict:
        transaction_values = self._get_tx_create_values(data, provider_sudo)
        tx_sudo = (
            self.env["payment.transaction"]
            .sudo()
            .with_context(
                shopinvader_api_payment=True,
                shopinvader_api_payment_base_url=urljoin(
                    str(request.url), "providers/"
                ),
            )
            .create(transaction_values)
        )
        return tx_sudo

    def _get_tx_processing_values(
        self, tx_sudo: PaymentTransaction, **kwargs: Any
    ) -> TransactionProcessingValues:
        """
        Extract the creation of the response to allow to extend it.
        """
        tx_values = tx_sudo._get_processing_values()
        # future:
        tx_values.pop("should_tokenize")
        return TransactionProcessingValues(flow="redirect", **tx_values)

    def _decode_payable(self, payable: str) -> Payable:
        try:
            return Payable.decode(self.env, payable)
        except Exception as e:
            _logger.info("Could not decode payable")
            raise HTTPException(403) from e

    def _get_providers_methods(self, payable_obj: Payable):
        # This method is similar to Odoo's PaymentPortal.payment_pay
        availability_report = {}
        providers_sudo = (
            self.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                payable_obj.company_id,
                payable_obj.partner_id,
                payable_obj.amount,
                report=availability_report,
                currency_id=payable_obj.currency_id,
            )
        )
        payment_methods_sudo = (
            self.env["payment.method"]
            .sudo()
            ._get_compatible_payment_methods(
                providers_sudo.ids,
                payable_obj.partner_id,
                report=availability_report,
            )
        )
        return providers_sudo, payment_methods_sudo

    def _handle_payment_flow(
        self,
        data: TransactionCreate,
        payable_obj: Payable,
        request: Request,
    ) -> TransactionProcessingValues:
        # similar to Odoo's /payment/transaction route
        if data.flow == "redirect":
            return self._handle_redirect_payment_flow(data, payable_obj, request)

    def _handle_redirect_payment_flow(
        self,
        data: TransactionCreate,
        payable_obj: Payable,
        request: Request,
    ) -> TransactionProcessingValues:
        providers_sudo, payment_methods_sudo = self._get_providers_methods(payable_obj)
        provider_sudo = providers_sudo.filtered(lambda p: p.id == data.provider_id)
        if not provider_sudo:
            _logger.info(
                "Invalid provider %s for partner %s",
                data.provider_id,
                payable_obj.partner_id,
            )
            raise HTTPException(403)

        payment_method_sudo = payment_methods_sudo.filtered(
            lambda m: m.id == data.payment_method_id
        )
        if not payment_method_sudo:
            _logger.info(
                "Invalid payment method %s for partner %s",
                data.payment_method_id,
                payable_obj.partner_id,
            )
            raise HTTPException(403)

        # Create the transaction
        tx_sudo = self._create_transaction(data, provider_sudo, request)
        tx_sudo._log_sent_message()

        return self._get_tx_processing_values(
            tx_sudo,
            payable=data.payable,
            frontend_redirect_url=data.frontend_redirect_url,
        )


def payment_helper(
    env: Annotated[api.Environment, Depends(odoo_env)],
):
    return env["shopinvader_api_payment.payment_router.helper"].new()


@payment_router.get("/payment/methods")
def pay(
    payable: str,
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
) -> PaymentDataWithMethods:
    """Available payment providers for the given encoded payment data.

    This route is public, so it is possible to pay anonymously provided that the
    parameters are obtained securely by another mean. An authenticated user can
    obtain the parameters with corresponding routes on the related payable
    objects (/cart/current/payable for e.g.).
    """
    payable_obj = helper._decode_payable(payable)
    providers_sudo, payment_methods_sudo = helper._get_providers_methods(payable_obj)

    return PaymentDataWithMethods(
        payable=payable,
        payable_reference=payable_obj.payable_reference,
        amount=payable_obj.amount,
        currency_code=helper.env["res.currency"].browse(payable_obj.currency_id).name,
        # We assume that the payable model has a currency field.
        # This shouldn't be a big assumption
        amount_formatted=helper.env[payable_obj.payable_model]
        .sudo()
        .browse(payable_obj.payable_id)
        .currency_id.format(payable_obj.amount),
        providers=[
            PaymentProviderSchema.from_payment_provider(provider, payment_methods_sudo)
            for provider in providers_sudo
        ],
    )


@payment_router.post("/payment/transactions")
def transaction(
    data: TransactionCreate,
    request: Request,
    helper: Annotated[PaymentHelper, Depends(payment_helper)],
) -> TransactionProcessingValues:
    """Create a payment transaction.

    Input is data obtained from /payment/providers, with the provider selected by the
    user. This route is public, so it is possible to pay anonymously.

    This route will automatically redirect to the return route linked to
    the specified provider. The user will finally land on data.frontend_redirect_url
    """
    payable_obj = helper._decode_payable(data.payable)

    rv = helper._handle_payment_flow(data, payable_obj, request)
    if not rv:
        raise NotImplementedError(
            helper.env._("{flow} flow is supported").format(flow=data.flow)
        )
    return rv
