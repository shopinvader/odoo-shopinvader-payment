# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    payment_acquirer_id = fields.Many2one(
        comodel_name="payment.acquirer", string="Payment Acquirer"
    )
