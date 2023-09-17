#  Copyright 2023 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import http

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class PaymentServiceListMethod(AbstractComponent):
    _name = "payment.service.list"
    _inherit = "base.rest.service"
    _usage = "payment_list_method"
    _description = "REST Services list of payment methods"

    @restapi.method(
        [(["/"], "GET")],
        output_param=restapi.CerberusValidator(
            "_get_schema_return_list_payment_method"
        ),
        cors="*",
    )
    def list_payment_method(self, **params):
        """Generates a list of available payment methods"""
        shopinvader_payments_released = (
            self.shopinvader_backend.payment_method_ids
        )
        if not shopinvader_payments_released:
            msg = "No payment providers added on Shopinvader Backend"
            _logger.error(msg)
            return http.Response(msg)

        list_payment_methods = []
        for shopinvader_payment_id in shopinvader_payments_released:
            methods_payment_ids = self.env["account.payment.method"].search(
                [
                    (
                        "provider",
                        "=",
                        shopinvader_payment_id.acquirer_id.provider,
                    )
                ]
            )
            acquirer_name = shopinvader_payment_id.acquirer_id.name

            provider_methods = []
            for method in methods_payment_ids:
                method_data = {
                    "id": method.id,
                    "name": method.name,
                    "code": method.code,
                }
                provider_methods.append(method_data)

            payment_method = {
                "provider": acquirer_name,
                "method": provider_methods,
            }

            list_payment_methods.append(payment_method)

        return {"list_payment_methods": list_payment_methods}

    def _get_schema_return_list_payment_method(self):
        return {
            "list_payment_methods": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "provider": {
                            "type": "string",
                            "required": True,
                            "nullable": True,
                        },
                        "method": {
                            "type": "list",
                            "schema": {
                                "type": "dict",
                                "schema": {
                                    "id": {
                                        "type": "integer",
                                        "min": 1,
                                        "required": True,
                                        "nullable": True,
                                    },
                                    "name": {
                                        "type": "string",
                                        "required": True,
                                        "nullable": True,
                                    },
                                    "code": {
                                        "type": "string",
                                        "required": True,
                                        "nullable": True,
                                    },
                                },
                            },
                        },
                    },
                },
            }
        }
