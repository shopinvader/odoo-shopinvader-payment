# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from Adyen.util import is_valid_hmac_notification
from odoo import _, fields, models

from ..services.exceptions import AdyenInvalidData

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    adyen_api_key = fields.Char(groups="base.group_user")
    adyen_live_endpoint_prefix = fields.Char(
        groups="base.group_user",
        help="You need to fill this in when switching to live environment. "
        "See: https://docs.adyen.com/development-resources/"
        "live-endpoints#set-up-live-endpoints",
    )

    def _get_adyen_notification_message(self, transaction, notification_item):
        message = transaction.state_message
        notification_message = "eventCode: {}, merchantReference: {}, pspReference: {}".format(
            notification_item.get("eventCode"),
            notification_item.get("merchantReference"),
            notification_item.get("pspReference"),
        )
        stamp = fields.Datetime.now()
        adyen_message = "\n" + stamp + ": " + str(notification_message)
        if message:
            message += adyen_message
        else:
            message = adyen_message
        return message

    def _get_adyen_additional_data(self, transaction, notification_item):
        """Allows to update transaction details with additional data
        comming from Adyen.

        :param transaction: [description]
        :type transaction: [type]
        :param notification_item: [description]
        :type notification_item: [type]
        """
        vals = {}
        message = self._get_adyen_notification_message(
            transaction, notification_item
        )
        vals.update({"state_message": message})
        return vals

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
        merchant_reference = notification_item.get("merchantReference")
        transaction = self.env["payment.transaction"].search(
            [("acquirer_reference", "=", psp_reference)]
        )
        if not transaction and merchant_reference:
            # If the transaction hasn't been validated but already created
            # by the paymentMethods call.
            transaction = self.env["payment.transaction"].search(
                [("reference", "=", merchant_reference)]
            )
        if len(transaction) != 1:
            message = _(
                "No payment transaction found with pspReference: %s"
                % psp_reference
            )
            _logger.warning(message)
            raise AdyenInvalidData(message)
        if not is_valid_hmac_notification(
            notification_item, transaction.acquirer_id.adyen_skin_hmac_key
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
            success = True if success == "true" else False
            if success and transaction.state != "done":
                # Set to done if not already. Don't raise, just pass
                # It will return a 200 code to Adyen, so the webhook will
                # be marked as done on their side.
                transaction._set_transaction_done()
            elif not success and transaction.state == "draft":
                # Set to error if draft. Don't raise, just pass
                # It will return a 200 code to Adyen, so the webhook will
                # be marked as done on their side.
                transaction._set_transaction_error(
                    self._get_adyen_notification_message(
                        transaction, notification_item
                    )
                )
        data = self._get_adyen_additional_data(transaction, notification_item)
        if data:
            transaction.write(data)
