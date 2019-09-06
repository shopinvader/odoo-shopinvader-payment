# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from cerberus import Validator
from openerp.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class PaymentManual(AbstractComponent):

    _name = "payment.service.manual"
    _inherit = "base.rest.service"
    _usage = "payment_manual"
    _description = (
        "REST Services for manual payments (bank transfer, check...)"
    )

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
        transaction_obj = self.env["payment.transaction"]
        payable = self.component(
            usage="invader.payment"
        )._invader_find_payable_from_target(target, **params)
        payment_mode = self.env["account.payment.mode"].browse(
            int(payment_mode)
        )
        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(payment_mode)
        )
        payable._invader_payment_start(transaction, payment_mode)
        transaction.write({"state": "pending"})
        payable._invader_payment_accepted(transaction)
        res = self.component(
            usage="invader.payment"
        )._invader_get_payment_success_reponse_data(payable, target, **params)
        return res
