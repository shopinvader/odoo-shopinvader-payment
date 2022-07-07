# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [_name, "invader.payable"]

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
        vals = {
            "amount": self.amount_residual,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "acquirer_id": acquirer_id.id,
            "invoice_ids": [(6, 0, self.ids)],
        }
        return vals

    def _invader_set_payment_mode(self, payment_mode):
        self.ensure_one()
        vals = {"payment_mode_id": payment_mode.id}
        newvals = self.play_onchanges(vals, vals.keys())
        vals.update(newvals)
        self.write(vals)

    def _invader_get_transactions(self):
        return self.transaction_ids
