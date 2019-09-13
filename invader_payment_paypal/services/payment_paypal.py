# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import requests
from cerberus import Validator
from odoo import _
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PAYPAL_ERROR = {"invalid_client": _("Invalid Paypal Credential")}

PAYPAL_STATUS = {
    "CREATED": "draft",
    "SAVED": "draft",
    "APPROVED": "pending",
    "VOIDED": "error",
    "COMPLETED": "done",
}


class PaymentServicePaypal(AbstractComponent):

    _name = "payment.service.paypal"
    _inherit = "base.rest.service"
    _usage = "payment_paypal"
    _description = "REST Services for Paypal payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _validator_checkout_order(self):
        """
        Validator of confirm_payment service
        target: see _allowed_payment_target()
        payment_mode_id: The payment mode used to pay
        :return: dict
        """
        res = self.payment_service._invader_get_target_validator()
        res.update(
            {
                "payment_mode_id": {
                    "coerce": to_int,
                    "type": "integer",
                    "required": True,
                },
                "return_url": {"type": "string", "required": True},
                "cancel_url": {"type": "string", "required": True},
            }
        )
        return res

    def _validator_return_checkout_order(self):
        schema = {"redirect_to": {"type": "string"}}
        return Validator(schema, allow_unknown=True)

    def _get_api_url(self, acquirer, path):
        if acquirer.environment == "prod":
            return "https://api.paypal.com/{}".format(path)
        else:
            return "https://api.sandbox.paypal.com/{}".format(path)

    def _catch_paypal_error(self, response):
        data = response.json()
        if data:
            if data.get("error") in PAYPAL_ERROR:
                raise UserError(PAYPAL_ERROR[data["error"]])
            if data.get("error_description"):
                raise UserError(data["error_description"])
            if data.get("message"):
                raise UserError(data["message"])
        raise UserError(response.content)

    def _get_api_token(self, acquirer):
        response = requests.post(
            self._get_api_url(acquirer, "v1/oauth2/token"),
            headers={"Accept": "application/json"},
            auth=(acquirer.paypal_client_id, acquirer.paypal_secret),
            params={"grant_type": "client_credentials"},
        )
        if response.status_code != 200:
            self._catch_paypal_error(response)
        data = response.json()
        return "{} {}".format(data["token_type"], data["access_token"])

    def _create_paypal_order(self, acquirer, data):
        token = self._get_api_token(acquirer)
        response = requests.post(
            self._get_api_url(acquirer, "v2/checkout/orders"),
            headers={
                "Content-Type": "application/json",
                "Authorization": token,
            },
            json=data,
        )
        if response.status_code != 201:
            self._catch_paypal_error(response)
        return response.json()

    def _prepare_paypal_order(
        self, transaction, return_url, cancel_url, **params
    ):
        return {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": transaction.currency_id.name,
                        "value": transaction.amount,
                    }
                }
            ],
            "application_context": {
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url,
            },
        }

    def checkout_order(
        self, target, payment_mode_id, return_url, cancel_url, **params
    ):
        transaction_obj = self.env["payment.transaction"]
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        payment_mode = self.env["account.payment.mode"].browse(payment_mode_id)
        self.payment_service._check_provider(payment_mode, "paypal")

        transaction = transaction_obj.create(
            payable._invader_prepare_payment_transaction_data(payment_mode)
        )
        payable._invader_set_payment_mode(payment_mode)
        data = self._prepare_paypal_order(
            transaction, return_url, cancel_url, **params
        )
        paypal_order = self._create_paypal_order(transaction.acquirer_id, data)
        transaction.write({"acquirer_reference": paypal_order["id"]})
        for link in paypal_order["links"]:
            if link["rel"] == "approve":
                return {"redirect_to": link["href"]}
        # In case of success paypal always provide the approve url
        # Passing in the following code should never happen
        _logger.error("Invalid Paypal response {}".format(paypal_order))
        raise UserError(_("Fail to create the payment"))

    def _validator_normal_return(self):
        schema = {
            "token": {"type": "string"},
            "success_redirect": {"type": "string"},
            "cancel_redirect": {"type": "string", "required": True},
        }
        schema.update(self.payment_service._invader_get_target_validator())
        return Validator(schema, allow_unknown=True)

    def _validator_return_normal_return(self):
        schema = {"redirect_to": {"type": "string"}}
        return Validator(schema, allow_unknown=True)

    def _capture_transaction(self, transaction, raise_error=False):
        acquirer = transaction.acquirer_id
        token = self._get_api_token(acquirer)
        response = requests.post(
            self._get_api_url(
                acquirer,
                "v2/checkout/orders/{}/capture".format(
                    transaction.acquirer_reference
                ),
            ),
            headers={
                "Content-Type": "application/json",
                "Authorization": token,
            },
        )
        if response.status_code != 201:
            try:
                self._catch_paypal_error(response)
            except UserError as e:
                if raise_error:
                    raise
                else:
                    transaction._set_transaction_error(e.name)
        else:
            state = PAYPAL_STATUS.get(response.json()["status"])
            if state == "done":
                transaction._set_transaction_done()
            else:
                transaction.write({"state": state})
        return True

    def _process_response(self, **params):
        transaction = self.env["payment.transaction"].search(
            [
                ("acquirer_reference", "=", params["token"]),
                ("acquirer_id.provider", "=", "paypal"),
            ]
        )
        if len(transaction) != 1:
            _logger.warning(
                "transaction with reference '%s' not found in "
                "Paypal automatic response",
                transaction.acquirer_reference,
            )
            raise UserError(_("Invalid data"))
        if transaction.state == "draft":
            # if transaction is not draft, it means it has already been
            # processed by webhook or normal_return
            self._capture_transaction(transaction)
        return transaction

    def normal_return(self, success_redirect, cancel_redirect, **params):
        """
        Service invoked in the user session, when the user returns to the
        merchant site from the Paypal payment site. It must return a redirect_to
        to the success or cancel url depending on transaction outcome.
        """
        _logger.info("Paypal normal_return: %s", params)
        transaction = self._process_response(**params)
        res = {}
        if transaction.state == "done":
            res["redirect_to"] = success_redirect
        else:
            res["redirect_to"] = cancel_redirect
        return res
