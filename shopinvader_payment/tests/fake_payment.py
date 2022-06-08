# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from cerberus import Validator

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent, Component


class FakePaymentManual(AbstractComponent):

    _name = "payment.service.manual.fake"
    _inherit = "base.rest.service"
    _usage = "fake_payment_manual"
    _description = "REST Services for fake manual payments"

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

    @restapi.method(
        [(["/add_payment"], "POST")],
        input_param=restapi.CerberusValidator(
            Validator(
                {
                    "target": {"type": "string", "required": True},
                    "payment_mode_id": {"type": "integer", "required": True},
                },
                allow_unknown=True,
            )
        ),
        output_param=restapi.CerberusValidator(Validator({})),
    )
    def add_payment(self, target, payment_mode_id, **params):
        """Prepare data for Manual payment submission"""
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )
        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        self.payment_service._check_provider(acquirer, "manual")

        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(acquirer)
        )
        transaction._set_transaction_pending()
        return {}


class FakePaymentElectronic(AbstractComponent):

    _name = "payment.service.electronic.fake"
    _inherit = "base.rest.service"
    _usage = "fake_payment_electronic"
    _description = "REST Services for fake electronic payments"

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

    @restapi.method(
        [(["/add_payment"], "POST")],
        input_param=restapi.CerberusValidator(
            Validator(
                {
                    "target": {"type": "string", "required": True},
                    "payment_mode_id": {"type": "integer", "required": True},
                },
                allow_unknown=True,
            )
        ),
        output_param=restapi.CerberusValidator(Validator({})),
    )
    def add_payment(self, target, payment_mode_id, **params):
        """Prepare data for Manual payment submission"""
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )
        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        self.payment_service._check_provider(acquirer, "manual")

        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(acquirer)
        )
        transaction._set_transaction_done()
        return {}


class PaymentServiceElectronicShopinvader(Component):

    # expose bank transfer payment service under /shopinvader

    _name = "payment.service.electronic.fake.shopinvader"
    _inherit = ["payment.service.electronic.fake", "base.shopinvader.service"]
    _usage = "fake_payment_electronic"
    _collection = "shopinvader.backend"


class PaymentServiceManualShopinvader(Component):

    # expose bank transfer payment service under /shopinvader

    _name = "payment.service.manual.fake.shopinvader"
    _inherit = ["payment.service.manual.fake", "base.shopinvader.service"]
    _usage = "fake_payment_manual"
    _collection = "shopinvader.backend"
