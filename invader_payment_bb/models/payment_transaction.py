# Copyright 2023 KMEE
# Lisence AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    tx_id = fields.Char(string="Tx Id")
