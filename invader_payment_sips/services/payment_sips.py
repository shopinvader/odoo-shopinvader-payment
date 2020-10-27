# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import dateutil
import logging
from hashlib import sha256

from cerberus import Validator
from odoo import _, fields
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SIPS_CURRENCY_CODES = {
    "EUR": ("978", 100),
    "USD": ("840", 100),
    "CHF": ("756", 100),
    "GBP": ("826", 100),
    "CAD": ("124", 100),
    "JPY": ("392", 100),
    "MXN": ("484", 100),
    "TRY": ("949", 100),
    "AUD": ("036", 100),
    "NZD": ("554", 100),
    "NOK": ("578", 100),
    "BRL": ("986", 100),
    "ARS": ("032", 100),
    "KHR": ("116", 100),
    "TWD": ("901", 100),
}


def _sips_make_seal(data, secret_key):
    # /!\ secret key stays on server
    return sha256((data + secret_key).encode("utf-8")).hexdigest()


def _sips_seal_check(data, seal, secret_key):
    return _sips_make_seal(data, secret_key) == seal


def _sips_parse_data(data_str):
    data_o = {}
    for item in data_str.split("|"):
        k, v = item.split("=", 1)
        data_o[k] = v
    return data_o


def _sips_make_data(data):
    return "|".join("{}={}".format(k, v) for (k, v) in data.items())


class PaymentServiceSips(AbstractComponent):

    _name = "payment.service.sips"
    _inherit = "base.rest.service"
    _usage = "payment_sips"
    _description = "REST Services for SIPS payments"

    @property
    def payment_service(self):
        return self.component(usage="invader.payment")

    def _validator_prepare_payment(self):
        # payment_mode_id: payment.acquirer id. Will be changed to acquirer_id.
        # Let to ensure backward compatibility
        schema = {
            "payment_mode_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "normal_return_url": {"type": "string"},
            "automatic_response_url": {"type": "string"},
        }
        schema.update(self.payment_service._invader_get_target_validator())
        return schema

    def _validator_return_prepare_payment(self):
        return {
            "sips_form_action_url": {"type": "string"},
            "sips_data": {"type": "string"},
            "sips_seal": {"type": "string"},
            "sips_interface_version": {"type": "string"},
        }

    def prepare_payment(
        self,
        target,
        payment_mode_id,
        normal_return_url,
        automatic_response_url,
        **params
    ):
        """ Prepare data for SIPS payment submission """
        payable = self.payment_service._invader_find_payable_from_target(
            target, **params
        )

        acquirer = self.env["payment.acquirer"].browse(payment_mode_id)
        self.payment_service._check_provider(acquirer, "sips")

        transaction_data = payable._invader_prepare_payment_transaction_data(acquirer)

        transaction = self.env["payment.transaction"].create(transaction_data)
        data = _sips_make_data(
            self._prepare_sips_data(
                transaction, normal_return_url, automatic_response_url
            )
        )
        seal = _sips_make_seal(data, acquirer.sips_secret)
        return {
            "sips_form_action_url": acquirer.sips_get_form_action_url(),
            "sips_data": data,
            "sips_seal": seal,
            "sips_interface_version": acquirer.sips_version,
        }

    def _prepare_sips_data(
        self, transaction, normal_return_url, automatic_response_url
    ):
        # https://documentation.sips.worldline.com/en/WLSIPS.001-GD-Data-dictionary.html
        acquirer = transaction.acquirer_id
        assert acquirer.provider == "sips"
        data = {}

        currency_code, currency_mult = SIPS_CURRENCY_CODES[
            transaction.currency_id.name
        ]
        data["amount"] = int(transaction.amount * currency_mult)
        data["currencyCode"] = currency_code
        data["transactionReference"] = transaction.reference
        data["merchantId"] = acquirer.sips_merchant_id
        data["keyVersion"] = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sips.key_version", "2")
        )
        data["normalReturnUrl"] = normal_return_url
        data["automaticResponseUrl"] = automatic_response_url
        return data

    def _validator_automatic_response(self):
        schema = {
            "Data": {"type": "string"},
            "Seal": {"type": "string"},
            "InterfaceVersion": {"type": "string"},
        }
        return Validator(schema, allow_unknown=True)

    def _validator_return_automatic_response(self):
        return {}

    def _process_response(self, **params):
        INVALID_DATA = _("invalid data")
        data = params.get("Data")
        seal = params.get("Seal")
        if not data or not seal:
            _logger.warning(
                "invalid SIPS automatic response: missing data or seal"
            )
            raise UserError(INVALID_DATA)
        data_o = _sips_parse_data(data)
        reference = data_o.get("transactionReference")
        if not reference:
            _logger.warning(
                "no transaction reference in SIPS automatic response"
            )
            raise UserError(INVALID_DATA)
        transaction = self.env["payment.transaction"].search(
            [("reference", "=", reference)]
        )
        if len(transaction) != 1:
            _logger.warning(
                "transaction with reference '%s' not found in "
                "SIPS automatic response",
                reference,
            )
            raise UserError(INVALID_DATA)
        acquirer = transaction.acquirer_id
        if acquirer.provider != "sips":
            _logger.warning(
                "transaction with reference '%s' has wrong provider "
                "in SIPS automatic response"
            )
            raise UserError(INVALID_DATA)
        if not _sips_seal_check(data, seal, acquirer.sips_secret):
            _logger.warning(
                "invalid seal '%s' for data '%s' in SIPS automatic response",
                seal,
                data,
            )
            raise UserError(INVALID_DATA)
        if transaction.state == "draft":
            # if transaction is not draft, it means it has already been
            # processed by automatic_response or normal_return
            response_code = data_o.get("responseCode")
            success = response_code == "00"
            transaction_date_time = data_o.get("transactionDateTime", fields.Datetime.now())
            if isinstance(transaction_date_time, str):
                transaction_date_time = dateutil.parser.parse(transaction_date_time).replace(tzinfo=None)
            tx_data = {
                # XXX better field for acquirer_reference?
                "acquirer_reference": data_o.get("transactionReference"),
                "date": transaction_date_time,
                "state_message": "SIPS response_code {}".format(response_code),
            }
            transaction.write(tx_data)
            if success:
                transaction._set_transaction_done()
            else:
                # XXX we may need to handle pending state?
                transaction._set_transaction_cancel()
        return transaction

    def automatic_response(self, **params):
        """
        Service as a callback by SIPS (therefore NOT in the user transaction)
        with information on the transaction outcome.
        """
        _logger.info("SIPS automatic_response: %s", params)
        self._process_response(**params)
        return {}

    def _validator_normal_return(self):
        schema = {
            "Data": {"type": "string"},
            "Seal": {"type": "string"},
            "InterfaceVersion": {"type": "string"},
            "success_redirect": {"type": "string"},
            "cancel_redirect": {"type": "string"},
        }
        schema.update(self.payment_service._invader_get_target_validator())
        return Validator(schema, allow_unknown=True)

    def _validator_return_normal_return(self):
        schema = {"redirect_to": {"type": "string"}}
        return Validator(schema, allow_unknown=True)

    def normal_return(
        self, target, success_redirect, cancel_redirect, **params
    ):
        """
        Service invoked in the user session, when the user returns to the
        merchant site from the SIPS payment site. It must return a redirect_to
        to the success or cancel url depending on transaction outcome.
        """
        _logger.info("SIPS normal_return: %s", params)
        transaction = self._process_response(**params)
        res = {}
        if transaction.state == "done":
            res["redirect_to"] = success_redirect
        else:
            res["redirect_to"] = cancel_redirect
        return res
