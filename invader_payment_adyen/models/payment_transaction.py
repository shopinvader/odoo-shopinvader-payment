# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_data = fields.Char(groups="base.group_user")
