# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.component.core import Component


class InvaderPaymentService(Component):

    _name = "invader.payment.service"
    _usage = "invader.payment"

    def _invader_find_payable_from_target(self, target, **params):
        """
        Find an invader.payable from a target parameter.

        :param params:
        :return:
        """
        raise NotImplementedError()

    def _invader_find_payable_from_transaction(self, transaction):
        """
        Find then invader.payble linked to a payment.transaction.
        """
        raise NotImplementedError()

    def _invader_get_target_validator(self):
        """
        Return a cerberus validator schema fragment that specifies the
        target being paid. Implementations must extend it by populating
        the "allowed" field (eg with strings such as 'current_cart') and
        possibly adding other fields.
        """
        return {"target": {"type": "string", "required": True, "allowed": []}}

    def _invader_get_payment_success_reponse_data(
        self, payable, target, **params
    ):
        """
        This is mostly used by ShopInvader to manipulate session and
        store_cache after payment success.
        """
        return {}
