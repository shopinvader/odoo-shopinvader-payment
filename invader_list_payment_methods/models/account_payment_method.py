# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountPaymentMethod(models.Model):

    _inherit = "account.payment.method"

    acquirer_id = fields.Many2one(
        "payment.acquirer", required=True, ondelete="restrict"
    )
