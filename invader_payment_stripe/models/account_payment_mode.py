# -*- coding: utf-8 -*-
# Copyright 2020 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    def _selection_capture_payment(self):
        res = super(AccountPaymentMode, self)._selection_capture_payment()
        res.append(("order_confirm", _("At Order Confirmation")))
        return res
