# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class InvaderPayable(models.AbstractModel):

    _name = "invader.payable"
    _description = "Provides base methods for payable models"

    def _invader_prepare_payment_transaction_data(self, payment_mode):
        """
        Prepare a dictionary to create a payment.transaction for the
        correct amount and linked to the payable object.
        :return:
        """

    def _invader_get_available_payment_methods(self):
        """
        Should be implemented on payable models level.
        :return: recordset (account.payment.method)
        """
        raise NotImplementedError

    def _invader_payment_start(self, transaction, payment_mode_id):
        """ Called just after the transaction has been created. """
        pass

    def _invader_payment_success(self, transaction):
        """ Called when the payment transaction succeeded. """
        pass
