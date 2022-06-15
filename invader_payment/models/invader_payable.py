# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class InvaderPayable(models.AbstractModel):

    _name = "invader.payable"
    _description = "Interface for payable objects (e.g. cart, ...)"

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        """
        Prepare a dictionary to create a ``payment.transaction`` for the
        correct amount and linked to the payable object.

        :param acquirer_id: ``payment.acquirer`` record
        :return: dictionary suitable for ``payment.transaction`` ``create()``
        """

    def _invader_get_transactions(self):
        """
        Return payment transaction recordset depending on the payable model
        """
