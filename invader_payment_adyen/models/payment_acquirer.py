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
        # Keep the function for backward compatibility
        return transaction._get_adyen_notification_message(notification_item)

    def _get_adyen_additional_data(self, transaction, notification_item):
        """Allows to update transaction details with additional data
        comming from Adyen.

        :param transaction: [description]
        :type transaction: [type]
        :param notification_item: [description]
        :type notification_item: [type]
        """
        vals = {}
        message = transaction._get_adyen_notification_message(
            notification_item
        )
        vals.update({"state_message": message})
        if not transaction.acquirer_reference:
            vals.update(
                {"acquirer_reference": notification_item.get("pspReference")}
            )
        if transaction.acquirer_id.provider == "adyen":
            payment_method = False
            if notification_item.get("action"):
                payment_method = notification_item.get("action")
                if isinstance(payment_method, dict):
                    payment_method = payment_method.get("paymentMethodType")
            if notification_item.get("paymentMethod"):
                payment_method = notification_item.get("paymentMethod")
                if isinstance(payment_method, dict):
                    payment_method = payment_method.get(
                        "brand"
                    ) or payment_method.get("type")
            if payment_method:
                vals.update({"adyen_payment_method": payment_method})
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
        addionalData = notification_item.get("additionalData")
        # Check if notification is for Ecommerce as you can have
        # notifications for POS too if using terminals
        # You have to add notification configuration in Adyen backend for
        # shopperInteraction (Include Shopper Interaction)
        if addionalData:
            shopperInteraction = addionalData.get("shopperInteraction")
            if shopperInteraction and shopperInteraction != "Ecommerce":
                return
        event_code = notification_item.get("eventCode")
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
            notification_item, transaction.acquirer_id.adyen_hmac_key
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

        data = self._get_adyen_additional_data(transaction, notification_item)
        if data:
            transaction.write(data)
        if event_code == "AUTHORISATION":
            transaction._handle_adyen_notification_item_authorized(
                notification_item
            )
        elif event_code == "REFUND":
            transaction._handle_adyen_notification_item_refund(
                notification_item
            )
        elif event_code == "CANCELLATION":
            transaction._handle_adyen_notification_item_cancel(
                notification_item
            )
        elif event_code == "CAPTURE":
            transaction._handle_adyen_notification_item_capture(
                notification_item
            )
        elif event_code == "CAPTURE_FAILED":
            transaction._handle_adyen_notification_item_capture_failed(
                notification_item
            )
