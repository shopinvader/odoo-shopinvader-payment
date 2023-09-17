# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountPaymentMethod(models.Model):

    _inherit = "account.payment.method"

    provider = fields.Selection(
        selection="_get_provider_options",
        string="Provider",
        required=True,
    )

    def _get_provider_options(self):
        payment_acquirer = self.env["payment.acquirer"]
        options = payment_acquirer.fields_get(["provider"])["provider"][
            "selection"
        ]
        return options
