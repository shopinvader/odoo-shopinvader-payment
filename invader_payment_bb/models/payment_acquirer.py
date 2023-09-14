# Copyright 2023 KMEE
# Lisence AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("BB", "Banco do Brasil")],
        required=True,
        ondelete={"BB": "set default"},
    )
