# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.exceptions import UserError


class InvaderPaymentService(Component):

    _inherit = "invader.payment.service"

    def _invader_find_payable_from_target(self, target, **params):
        if target == "quotation":
            quotation_id = params.get("quotation_id")
            if not quotation_id:
                raise UserError(_("Quotation id is missing"))
            quotation = self.component(usage="quotations")._get(quotation_id)
            if not quotation:
                raise UserError(_("The quotation doesn't exist"))
            elif quotation.state != "sent":
                raise UserError(_("The quotation is not yet estimated"))
            return quotation
        return super(
            InvaderPaymentService, self
        )._invader_find_payable_from_target(target, **params)

    def _invader_get_target_validator(self):
        res = super(
            InvaderPaymentService, self
        )._invader_get_target_validator()
        res["target"]["allowed"].append("quotation")
        res["quotation_id"] = {"coerce": to_int, "type": "integer"}
        return res
