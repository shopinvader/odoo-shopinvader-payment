# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import binascii
import hashlib
import hmac
import logging
from collections import OrderedDict

from odoo import _, fields, models

from ..services.exceptions import AdyenInvalidData

_logger = logging.getLogger(__name__)

ADYEN_PAYLOAD = [
    {"key": 1, "value": "pspReference"},
    {"key": 2, "value": "originalReference"},
    {"key": 3, "value": "merchantAccountCode"},
    {"key": 4, "value": "merchantReference"},
    {"key": 5, "value": "amount"},
    {"key": 7, "value": "eventCode"},
    {"key": 8, "value": "success"},
]


def escape_vals(val):
    if isinstance(val, int):
        return val
    return val.replace("\\", "\\\\").replace(":", "\\:")


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    adyen_api_key = fields.Char(groups="base.group_user")
    adyen_live_endpoint_prefix = fields.Char(
        groups="base.group_user",
        help="You need to fill this in when switching to live environment. "
        "See: https://docs.adyen.com/development-resources/"
        "live-endpoints#set-up-live-endpoints",
    )

    def _check_adyen_payload_hmac(self, notification_data):
        """
        Reimplement Adyen signature generation as it appeared to be buggy
        TODO: Check Adyen lib updates
        :param notification_data:
        :return:
        """
        self.ensure_one()
        payload = OrderedDict()
        hmac_signature = notification_data.get("additionalData").get(
            "hmacSignature"
        )
        hmac_key = binascii.a2b_hex(self.adyen_skin_hmac_key)
        for item in sorted(ADYEN_PAYLOAD, key=lambda k: k["key"]):
            adyen_payload = item.get("value")
            if adyen_payload == "amount":
                value = notification_data.get("amount").get("value")
                currency = notification_data.get("amount").get("currency")
                payload.update({"value": value})
                payload.update({"currency": currency})
            else:
                data = notification_data.get(adyen_payload, "")
                payload.update({adyen_payload: data})

        string = ":".join(
            [str(escape_vals(pay)) for key, pay in payload.iteritems()]
        )
        _logger.debug(_("Encoding Adyen Payload: %s"), string)
        digest = base64.b64encode(
            hmac.new(str(hmac_key), string, hashlib.sha256).digest()
        )
        return digest == hmac_signature

    def _handle_adyen_notification_item(self, notification_item):
        """
        https://docs.adyen.com/development-resources/notifications/
        verify-hmac-signatures#example
        Look for a transaction with acquirer_reference == pspReference
        Raise if none or > 1 transaction found or if transaction is not an
        Adyen one
        Then confirm the transaction
        :param notification_item:
        :return:
        """
        if "pspReference" not in notification_item:
            message = _("pspReference not in webhook data!")
            _logger.warning(message)
            raise AdyenInvalidData(message)
        psp_reference = notification_item.get("pspReference")
        transaction = self.env["payment.transaction"].search(
            [("acquirer_reference", "=", psp_reference)]
        )
        if len(transaction) != 1:
            message = _(
                "No payment transaction found with pspReference: %s"
                % psp_reference
            )
            _logger.warning(message)
            raise AdyenInvalidData(message)
        if not transaction.acquirer_id._check_adyen_payload_hmac(
            notification_item
        ):
            message = _("Transaction Data is not safe!")
            _logger.warning(message)
            raise AdyenInvalidData(message)
        acquirer = transaction.acquirer_id
        if acquirer.provider != "adyen":
            message = _(
                "transaction with reference '%s' has wrong provider "
                "in Adyen automatic response" % psp_reference
            )
            _logger.warning(message)
            raise AdyenInvalidData(message)
        event_code = notification_item.get("eventCode")
        if event_code == "AUTHORISATION":
            success = notification_item.get("success")
            if success:
                transaction._set_transaction_done()
