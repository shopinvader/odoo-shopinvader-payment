# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pydantic import BaseModel

from .payment_brand import PaymentBrand


class PaymentProvider(BaseModel):
    id: int
    code: str
    name: str
    state: str
    inline_form_view_rendered: str | None
    express_checkout_form_view_rendered: str | None
    payment_icons: list[PaymentBrand] = []

    @classmethod
    def _get_rendered_views(cls, odoo_rec, rendering_values=None):
        express_form_view_id = odoo_rec.express_checkout_form_view_id
        return {
            "inline_form_view_rendered": odoo_rec.inline_form_view_id._render_template(
                odoo_rec.inline_form_view_id.id, rendering_values
            )
            if odoo_rec.inline_form_view_id
            else None,
            "express_checkout_form_view_rendered": express_form_view_id._render_template(  # noqa: E501
                express_form_view_id.id, rendering_values
            )
            if express_form_view_id
            else None,
        }

    @classmethod
    def from_payment_provider_method_brands(cls, provider, method, brands):
        # TODO: should we add more rendering values, for eg.
        # the ones returned by _get_default_payment_link_values() on
        # SO's and invoices?
        rendering_values = {
            "provider_sudo": provider,
        }
        rendered_views = cls._get_rendered_views(provider, rendering_values)
        return cls.model_construct(
            id=method.id,
            code=method.code,
            name=method.name,
            state=provider.state,
            inline_form_view_rendered=rendered_views.get("inline_form_view_rendered"),
            express_checkout_form_view_rendered=rendered_views.get(
                "express_checkout_form_view_rendered"
            ),
            payment_icons=[PaymentBrand.from_payment_brand(brand) for brand in brands],
        )
