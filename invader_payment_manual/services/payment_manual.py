# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError as err:
    _logger.debug(err)


class PaymentManual(AbstractComponent):

    _name = "payment.service.manual"
    _inherit = "base.rest.service"
    _usage = "payment_manual"
    _description = (
        "REST Services for manual payments (bank transfer, check...)"
    )

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _validator_add_payment(self):
        schema = {
            "payment_mode_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            }
        }
        schema.update(self.payment_service._invader_get_target_validator())
        return schema

    def _validator_return_add_payment(self):
        schema = {}
        return Validator(schema, allow_unknown=True)

    def add_payment(self, target, payment_mode_id, **params):
        """ Prepare data for Manual payment submission """
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )
        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)
        self.payment_service._check_provider(payment_mode, "transfer")

        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(payment_mode)
        )
        payable._invader_set_payment_mode(payment_mode)
        transaction.write({"state": "pending"})
        return {}
