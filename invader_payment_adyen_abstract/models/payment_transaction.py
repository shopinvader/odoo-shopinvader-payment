# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)
try:
    pass
except ImportError as err:
    _logger.debug(err)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_data = fields.Char(groups="base.group_user")
    adyen_payment_method = fields.Char()

    def _get_formatted_amount(self, force_amount=False):
        """
        The expected amount format by Adyen
        :param transaction: payment.transaction
        :param amount: float
        :return: int
        """
        value = super()._get_formatted_amount(force_amount=force_amount)
        if "adyen" in self.acquirer_id.provider:
            value = int(value * 100)
        return value

    def _prepare_adyen_session(self):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment
        Prepare payments request
        :return:
        """
        self.ensure_one()
        partner = self.partner_id
        lang = partner.lang or self.env.lang or "en_US"
        request = {
            "merchantAccount": self._get_adyen_merchant_account(),
            "amount": {
                "value": self._get_formatted_amount(),
                "currency": self.currency_id.name,
            },
            "reference": self.reference,
            "countryCode": partner.country_id.code,
        }
        if lang:
            request.update({"shopperLocale": lang})
        if partner.email:
            request.update({"shopperEmail": partner.email})
        if self.return_url:
            request.update({"returnUrl": self.return_url})
        return request

    def _get_adyen_merchant_account(self):
        """
        Return adyen merchant account depending on
        payment.transaction recordset
        :return: string
        """
        raise NotImplementedError()

    def _get_adyen_notification_message(self, notification_item):
        message = self.state_message
        notification_message = (
            "eventCode: {}, merchantReference: {}, pspReference: {}".format(
                notification_item.get("eventCode"),
                notification_item.get("merchantReference"),
                notification_item.get("pspReference"),
            )
        )
        stamp = str(fields.Datetime.now())
        adyen_message = "\n" + stamp + ": " + str(notification_message)
        if message:
            message += adyen_message
        else:
            message = adyen_message
        return message

    def _handle_adyen_notification_item_authorized(self, notification_item):
        success = notification_item.get("success")
        success = True if success == "true" else False
        if success and self.state != "done" and self.state != "authorized":
            # Set to done if not already. Don't raise, just pass
            # It will return a 200 code to Adyen, so the webhook will
            # be marked as done on their side.
            self._set_transaction_done()
        elif not success and self.state == "draft":
            # Set to error if draft. Don't raise, just pass
            # It will return a 200 code to Adyen, so the webhook will
            # be marked as done on their side.
            self._set_transaction_error(
                self._get_adyen_notification_message(notification_item)
            )

    def _handle_adyen_notification_item_refund(self, notification_item):
        self.write(
            {
                "state_message": self._get_adyen_notification_message(
                    notification_item
                ),
            }
        )

    def _handle_adyen_notification_item_cancel(self, notification_item):
        self.write(
            {
                "state_message": self._get_adyen_notification_message(
                    notification_item
                )
            }
        )
        self._set_transaction_cancel()

    def _handle_adyen_notification_item_capture(self, notification_item):
        success = notification_item.get("success")
        success = True if success == "true" else False
        if success and self.state != "done":
            # Set to done if not already. Don't raise, just pass
            # It will return a 200 code to Adyen, so the webhook will
            # be marked as done on their side.
            self._set_transaction_done()
        elif not success and self.state == "draft":
            # Set to error if draft. Don't raise, just pass
            # It will return a 200 code to Adyen, so the webhook will
            # be marked as done on their side.
            self._set_transaction_error(
                self._get_adyen_notification_message(notification_item)
            )

    def _handle_adyen_notification_item_capture_failed(
        self, notification_item
    ):
        self._set_transaction_error(
            self._get_adyen_notification_message(notification_item)
        )
