# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class InvaderPayable(models.AbstractModel):

    _name = "invader.payable"
    _description = "Interface for payable objects (e.g. cart, ...)"

    def _invader_prepare_payment_transaction_data(self, payment_mode):
        """
        Prepare a dictionary to create a ``payment.transaction`` for the
        correct amount and linked to the payable object.

        :param payment_mode: ``account.payment.mode`` record
        :return: dictionary suitable for ``payment.transaction`` ``create()``
        """

    def _invader_set_payment_mode(self, payment_mode):
        """
        Called to set the payment_mode on the payable. The payable object can
        be notified if the transaction process by defining an event listener.
        see `òdoo.addons.ivader_payment.model.payment_transaction.
        PaymentTransaction`
        """
        pass
