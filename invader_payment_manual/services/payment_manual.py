# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from cerberus import Validator
from odoo import _
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentManual(AbstractComponent):

    _name = "payment.service.manual"
    _inherit = "base.rest.service"
    _usage = "payment_manual"
    _description = (
        "REST Services for manual payments (bank transfer, check...)"
    )

    def _validator_add_payment(self):
        schema = {
            "payment_mode_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            }
        }
        schema.update(
            self.component(
                usage="invader.payment"
            )._invader_get_target_validator()
        )
        return schema

    def _validator_return_add_payment(self):
        schema = {}
        return Validator(schema, allow_unknown=True)

    def add_payment(self, target, payment_mode_id, **params):
        """ Prepare data for Manual payment submission """
        transaction_obj = self.env["payment.transaction"]
        payable = self.component(
            usage="invader.payment"
        )._invader_find_payable_from_target(target, **params)
        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)

        acquirer = payment_mode.payment_acquirer_id.sudo()
        if acquirer.provider != "transfer":
            raise UserError(
                _(
                    "Payment mode acquirer mismatch should be "
                    "'transfer' instead of {}."
                ).format(acquirer.provider)
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
