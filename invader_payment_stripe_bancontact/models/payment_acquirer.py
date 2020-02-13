# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentAcquirer(models.Model):

    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("stripe_bancontact", "Bancontact (Stripe)")]
    )
