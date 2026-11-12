# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .payment_data import PaymentInput


class TransactionCreate(PaymentInput):
    flow: Literal["redirect"]  # future: redirect|token
    # This is now a payment.method id, this is deprecated
    # and kept for backward compatibility,
    # use method_id instead
    provider_id: int | None = None
    method_id: int | None = None
    # payment_token_id: int (future)

    # A URL in the frontend where the user will be redirected to after
    # the trip to the payment provider. The following query parameter will be
    # added to the URL: status (success|cancelled|unknown|error)
    # and reference (the transaction reference)
    frontend_redirect_url: Annotated[
        str,
        Field(
            description="A URL in the frontend where the user will be "
            "redirected to after the trip to the payment provider. "
            "The following query parameters will be added to the URL: "
            "status (success|cancelled|pending|unknown|error) and "
            "reference (the transaction reference"
        ),
    ]

    # Ensure that either provider_id or method_id is set
    @model_validator(mode="before")
    def check_provider_id_or_method_id(cls, data):
        if not data.get("provider_id") and not data.get("method_id"):
            raise ValueError("Please provide a method_id")
        return data
