# -*- coding: utf-8 -*-
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

    def _invader_payment_start(self, transaction, payment_mode_id):
        """
        Called just after the transaction has been created.
        """
        pass

    def _invader_payment_accepted(self, transaction):
        """
        Called when the payment transaction has been accepted.

        This can be when the acquirer confirmed payment success, or
        in case of bank transfer or cheque, immediatelly after
        _invader_payment_start. This not necessarily mean that the
        payment is confirmed, but rather to signal that the front-end tunnel
        was successful.
        """
        pass
