# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    provider = fields.Selection(
        selection=[("pagseguro", "PagSeguro")],
        string="Provider",
        default="pagseguro",
        required=True,
    )
