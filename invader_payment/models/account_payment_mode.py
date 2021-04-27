# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    payment_acquirer_id = fields.Many2one(
        comodel_name="payment.acquirer", string="Payment Acquirer"
    )

    capture_payment = fields.Selection(
        selection="_selection_capture_payment",
        required=True,
        default="immediately",
    )

    def _selection_capture_payment(self):
        return [
            ("immediately", _("Immediately")),
            ("order_confirm", _("At Order Confirmation")),
            ("picking_confirm", _("At Picking Confirmation")),
        ]
