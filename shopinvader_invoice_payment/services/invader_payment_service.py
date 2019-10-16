# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class InvaderPaymentService(Component):
    _inherit = "shopinvader.payment.service"

    def _invader_find_payable_from_target(self, target, **params):
        if target == "invoice":
            invoice_id = params.get("invoice_id")
            return self.component(usage="invoice")._get(invoice_id)
        return super(
            InvaderPaymentService, self
        )._invader_find_payable_from_target(target, **params)

    def _invader_get_target_validator(self):
        schema = super(
            InvaderPaymentService, self
        )._invader_get_target_validator()
        schema["target"]["allowed"].append("invoice")
        schema.update(
            {
                "invoice_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": False,
                }
            }
        )
        return schema
