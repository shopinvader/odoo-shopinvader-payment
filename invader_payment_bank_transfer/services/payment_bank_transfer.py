# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from cerberus import Validator
from openerp.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class PaymentBankTransfer(AbstractComponent):

    _name = "payment.service.bank_transfer"
    _inherit = "base.rest.service"
    _usage = "payment_bank_transfer"
    _description = "REST Services for bank transfer payments"

    def _validator_add_payment(self):
        schema = {"payment_mode": {"type": "string"}}
        schema.update(
            self.component(
                usage="invader.payment"
            )._invader_get_target_validator()
        )
        return schema

    def _validator_return_add_payment(self):
        schema = {}
        return Validator(schema, allow_unknown=True)

    def add_payment(self, target, payment_mode, **params):
        """ Prepare data for SIPS payment submission """
        payable = self.component(
            usage="invader.payment"
        )._invader_find_payable_from_target(target, **params)
        payment_mode = self.env["account.payment.mode"].browse(
            int(payment_mode)
        )
        transaction = self.env["payment.transaction"].browse()
        payable._invader_payment_start(transaction, payment_mode)
        payable._invader_payment_success(transaction)
        res = self.component(
            usage="invader.payment"
        )._invader_get_payment_success_reponse_data(payable, target, **params)
        return res
