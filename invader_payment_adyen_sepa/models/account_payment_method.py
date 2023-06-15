# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    payment_acquirer_id = fields.Many2one(
        comodel_name="payment.acquirer",
        string="Acquirer",
    )
