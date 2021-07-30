# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [_name, "invader.payable"]

    def _invader_prepare_payment_transaction_data(self, payment_mode):
        self.ensure_one()
        allowed_payment_mode = self.shopinvader_backend_id.mapped(
            "payment_method_ids.payment_mode_id"
        )
        if payment_mode not in allowed_payment_mode:
            raise exceptions.UserError(
                _("Payment mode %s is not allowed on backend %s")
                % (payment_mode.name, self.shopinvader_backend_id.name)
            )
        vals = {
            "amount": self.residual,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "acquirer_id": payment_mode.payment_acquirer_id.id,
            "invoice_ids": [(6, 0, self.ids)],
        }
        return vals

    def _invader_set_payment_mode(self, payment_mode):
        self.ensure_one()
        vals = {"payment_mode_id": payment_mode.id}
        newvals = self.play_onchanges(vals, vals.keys())
        vals.update(newvals)
        self.write(vals)
