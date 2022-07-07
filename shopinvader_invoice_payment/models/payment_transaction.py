# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_invoice_not_payable_states(self):
        """
        Get invoice states where it's not possible to pay.
        :return: list of str
        """
        return ["paid", "cancel"]

    def _get_invader_payables(self):
        """
        Inherit to return invoices to pay
        :return: recordset
        """
        self.ensure_one()
        if self.invoice_ids:
            states = self._get_invoice_not_payable_states()
            return self.invoice_ids.filtered(lambda i: i.state not in states)
        return super()._get_invader_payables()