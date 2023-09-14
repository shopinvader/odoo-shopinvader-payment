#  Copyright 2023 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo.exceptions import UserError, ValidationError

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import AbstractComponent


class PaymentServicePagseguro(AbstractComponent):
    _name = "payment.service.bb"
    _inherit = "base.rest.service"
    _usage = "payment_bacen_pix"
    _description = "REST Services for Bank of Brazil payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _get_payable(self, target, params):
        """Get payable from current cart"""
        return self.payment_service._invader_find_payable_from_target(
            target, **params
        )

    def _get_payment_mode(self):
        """Returns payment mode from id.
        Checks if payment mode has Banck of Brazil acquirer.
        """
        payment_mode = self.env.ref(
            "payment_bacen_pix.payment_acquirer_bacenpix"
        )
        self.payment_service._check_provider(payment_mode, "bacenpix")

        return payment_mode

    def _create_transaction(self, payable, token, payment_mode_id, tx_id):
        """Creates and returns a transaction based on parameters."""
        transaction_data = payable._invader_prepare_payment_transaction_data(
            payment_mode_id
        )
        transaction_data["payment_token_id"] = token.id
        transaction_data["reference"] = payable.name
        transaction_data["tx_id"] = tx_id

        return self.env["payment.transaction"].create(transaction_data)

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
    def confirm_payment_pix(self, target, **params):
        acquirer = self._get_payment_mode()
        payable = self._get_payable(target, params)
        tx_id = params.get("tx_id")
        payment_mode = self.env.ref("invader_payment_bb.payment_mode_bb")
        token = self._get_token_pix(payable, acquirer)
        try:
            if re.search(r"[!#$%&*]", tx_id):
                return {"result": False, "error": "Invalid characters"}
            res = self._create_transaction(payable, token, acquirer, tx_id)
            # payable._invader_set_payment_mode(payment_mode) v12
            self._set_payment_mode(res, payment_mode)

        except (UserError, ValidationError) as e:
            return {"result": False, "error": str(e)}

        return {
            "calendario": {
                "criacao": str(res.bacenpix_criacao),
                "expiracao": res.bacenpix_expiracao,
            },
            "location": res.bacenpix_location,
            "textoImagemQRcode": res.textoImagemQRcode,
            "txid": res.bacenpix_txid,
            "chave": res.bacenpix_chave,
        }

    @staticmethod
    def _set_payment_mode(transaction, payment_mode):
        return transaction.sale_order_ids.update(
            {"payment_mode_id": payment_mode}
        )

    def _get_schema_return_confirm_payment_pix(self):
        return {
            "calendario": {
                "type": "dict",
                "required": False,
                "schema": {
                    "criacao": {"type": "string", "required": False},
                    "expiracao": {"type": "string", "required": False},
                },
            },
            "location": {"type": "string", "required": False},
            "textoImagemQRcode": {"type": "string", "required": False},
            "txid": {"type": "string", "required": False},
            "chave": {"type": "string", "required": False},
            "result": {"type": "boolean", "required": False},
            "error": {"type": "string", "required": False},
        }

    def _get_schema_confirm_payment_pix(self):
        res = self.payment_service._invader_get_target_validator()
        res.update({"tx_id": {"type": "string", "required": True}})
        return res

    def _get_token_pix(self, payable, acquirer):
        partner = payable.partner_id
        payment_token = (
            self.env["payment.token"]
            .sudo()
            .create(
                {
                    "acquirer_ref": partner.id,
                    "acquirer_id": acquirer.id,
                    "partner_id": partner.id,
                    "bb_payment_method": "PIX",
                }
            )
        )

        return payment_token
