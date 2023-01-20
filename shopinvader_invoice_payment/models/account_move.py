# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        self.ensure_one()
        allowed_acquirer = self.shopinvader_backend_id.mapped(
            "payment_method_ids.acquirer_id"
        )
        if acquirer_id not in allowed_acquirer:
            raise UserError(
                _("Acquirer %s is not allowed on backend %s")
                % (acquirer_id.name, self.shopinvader_backend_id.name)
            )
        return super()._invader_prepare_payment_transaction_data(acquirer_id)
