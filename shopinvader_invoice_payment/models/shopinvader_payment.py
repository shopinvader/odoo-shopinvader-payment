# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ShopinvaderPayment(models.Model):
    _inherit = "shopinvader.payment"

    notification = fields.Selection(
        selection_add=[
            ("invoice_confirmation", "Invoice confirmation"),
            ("invoice_paid", "Invoice paid"),
        ]
    )
