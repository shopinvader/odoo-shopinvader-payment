#  Copyright 2022 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

import requests

from odoo import http
from odoo.exceptions import UserError, ValidationError

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent


class PaymentServicePagseguro(AbstractComponent):
    _name = "payment.service.pagseguro"
    _inherit = "base.rest.service"
    _usage = "payment_pagseguro"
    _description = "REST Services for Pagseguro payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _get_payable(self, target, **params):
        """Get payable from current cart"""
        return self.payment_service._invader_find_payable_from_target(
            target, **params
        )

    def _get_payment_mode(self):
        """Returns payment mode from id.
        Checks if payment mode has Pagseguro acquirer.
        """
        payment_mode = self.env.ref(
            "invader_payment_pagseguro.payment_mode_pagseguro"
        )
        payment_mode.update({"company_id": self.env.company})
        self.payment_service._check_provider(payment_mode, "pagseguro")

        return payment_mode

    def _create_transaction(self, payable, payment_mode_id, token):
        """Creates and returns a transaction based on parameters."""
        transaction_data = payable._invader_prepare_payment_transaction_data(
            payment_mode_id
        )

        if token:
            transaction_data["payment_token_id"] = token.id

        return self.env["payment.transaction"].create(transaction_data)

    @restapi.method(
        [(["/confirm-payment-credit"], "POST")],
        input_param=restapi.CerberusValidator(
            "_get_schema_confirm_payment_credit"
        ),
        output_param=restapi.CerberusValidator(
            "_get_schema_return_confirm_payment_credit"
        ),
        cors="*",
    )
    def confirm_payment_credit(self, target, **params):
        """Create charge from payable sale order"""
        card = params.get("card")
        payment_mode = self._get_payment_mode()
        payable = self._get_payable(target, params)
        acquirer = self._get_payment_acquirer()
        token = self._get_token_credit(card, payable)
        transaction = self._create_transaction(payable, token, acquirer)
        transaction.pagseguro_s2s_do_transaction()
        self._set_payment_mode(transaction, payment_mode)

        return {
            "transaction_status": transaction.state,
        }

    @restapi.method(
        [(["/confirm-payment-pix"], "POST")],
        input_param=restapi.CerberusValidator(
            "_get_schema_confirm_payment_pix"
        ),
        output_param=restapi.CerberusValidator(
            "_get_schema_return_confirm_payment_pix"
        ),
        cors="*",
    )
    def confirm_payment_pix(self, target):
        # Get body params
        payment_mode = self._get_payment_mode()
        payable = self._get_payable(target)
        acquirer = self._get_payment_acquirer()
        transaction = self._create_transaction(payable, acquirer, False)
        try:
            res = transaction.pagseguro_pix_do_transaction("pix")
            self._set_payment_mode(transaction, payment_mode)
        except (UserError, ValidationError) as e:
            return {"result": False, "error": str(e)}
        if not res["result"]:
            status = int(res["status"][:3])
            return http.Response(res["error"], status=status)

        return res

    @restapi.method(
        [(["/confirm-payment-boleto"], "POST")],
        input_param=restapi.CerberusValidator(
            "_get_schema_confirm_payment_boleto"
        ),
        output_param=restapi.CerberusValidator(
            "_get_schema_return_confirm_payment_boleto"
        ),
        cors="*",
    )
    def confirm_payment_boleto(self, target, **params):
        """Confirm payment with Boleto.

        Creates a pagseguro charge and change the sale order status to authorized.
        Returns result True when Pagseguro's charge is created successfully.
        """
        payment_mode = self._get_payment_mode()
        payable = self._get_payable(target, params)
        token = self._get_token_boleto(payable)
        transaction = self._create_transaction(payable, token, payment_mode)

        try:
            res = transaction.pagseguro_boleto_do_transaction()
            self._set_payment_mode(transaction, payment_mode)
        except Exception as e:
            return {"res": {"error": str(e)}}

        return {"res": res}

    @restapi.method(
        [(["/public-key"], "GET")],
        input_param=restapi.CerberusValidator("_get_schema_public_key"),
        output_param=restapi.CerberusValidator(
            "_get_schema_return_public_key"
        ),
    )
    def public_key(self, target, **params):
        """Get public key to encrypt card

        return public_key (string): public key related to acquirer token
        """
        acquirer = self._get_payment_acquirer()
        payload = {"jsonrpc": "2.0", "params": {"acquirer_id": acquirer.id}}
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        res = requests.get(
            base_url + "/payment/pagseguro/public_key", json=payload
        )

        content = json.loads(res.content)
        if content.get("result"):
            return {
                "public_key": content.get("result"),
                "success": True,
            }
        elif content.get("error"):
            message = content.get("error", {}).get("data", {}).get("message")
            return {
                "public_key": "",
                "success": False,
                "error": message,
            }
        else:
            return {
                "public_key": "",
                "success": False,
                "error": "Unknown error",
            }

    def _get_token_credit(self, card, payable):
        acquirer = self._get_payment_acquirer()
        partner = payable.partner_id

        data = {
            "acquirer_id": acquirer.id,
            "partner_id": partner.id,
            "cc_holder_name": card.get("name"),
            "card_brand": card.get("brand"),
            "cc_token": card.get("token"),
            "payment_method": "CREDIT_CARD",
            "installments": card.get("installments"),
        }

        return acquirer.pagseguro_s2s_form_process(data)

    def _get_token_pix(self, payable, tx_id):
        acquirer = self._get_payment_acquirer()
        partner = payable.partner_id

        payment_token = (
            self.env["payment.token"]
            .sudo()
            .create(
                {
                    "name": payable.name,
                    "acquirer_ref": payable.name,
                    "acquirer_id": acquirer.id,
                    "partner_id": partner.id,
                }
            )
        )

        return payment_token

    def _get_token_boleto(self, payable):
        acquirer = self._get_payment_acquirer()
        partner = payable.partner_id

        payment_token = (
            self.env["payment.token"]
            .sudo()
            .create(
                {
                    "acquirer_ref": partner.id,
                    "acquirer_id": acquirer.id,
                    "partner_id": partner.id,
                    "pagseguro_payment_method": "BOLETO",
                }
            )
        )

        return payment_token

    def _get_schema_confirm_payment_credit(self):
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "card": {
                    "type": "dict",
                    "required": True,
                    "schema": {
                        "name": {"type": "string", "required": True},
                        "brand": {"type": "string", "required": False},
                        "token": {"type": "string", "required": True},
                        "installments": {
                            "type": "integer",
                            "coerce": int,
                            "required": True,
                        },
                    },
                },
            }
        )
        return res

    def _get_schema_return_confirm_payment_credit(self):
        return {
            "transaction_status": {"type": "string", "required": True},
        }

    def _get_schema_public_key(self):
        """Get default api key and user email validator"""
        return self.payment_service._invader_get_target_validator()

    def _get_schema_return_public_key(self):
        """
        Return validator of checkout_url service
        checkout_url (str): Redirect checkout url
        """
        return {
            "public_key": {"type": "string", "required": True},
            "success": {"type": "boolean", "required": True},
            "error": {"type": "string", "required": False},
        }

    def _get_schema_confirm_payment_pix(self):
        res = self.payment_service._invader_get_target_validator()
        # res.update({"tx_id": {"type": "string", "required": True}})
        return res

    def _get_schema_return_confirm_payment_pix(self):
        return {
            "result": {"type": "boolean", "required": True},
            "location": {"type": "string", "required": False},
            "error": {"type": "string", "required": False},
        }

    def _get_schema_confirm_payment_boleto(self):
        return self.payment_service._invader_get_target_validator()

    @staticmethod
    def _get_schema_return_confirm_payment_boleto():
        return {
            "res": {"type": "dict", "allow_unknown": True, "required": False}
        }

    def _get_payment_acquirer(self):
        return self.env.ref("payment_pagseguro.payment_acquirer_pagseguro")

    @staticmethod
    def _set_payment_mode(transaction, payment_mode):
        return transaction.sale_order_ids.update(
            {"payment_mode_id": payment_mode}
        )
