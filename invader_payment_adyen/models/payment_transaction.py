# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_data = fields.Char(groups="base.group_user")
    adyen_payment_method = fields.Char()

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

    def _get_platform(self):
        """
        For Adyen: return 'test' or 'live' depending on acquirer value
        :return: str
        """
        if self.acquirer_id.provider == "adyen":
            state = self.acquirer_id.state
            return "test" if state in ("disabled", "test") else "live"
        return super()._get_platform()

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
