# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)
try:
    import Adyen
except ImportError as err:
    _logger.debug(err)


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

    def _get_adyen_merchant_account(self):
        """
        Return adyen merchant account depending on
        payment.transaction recordset
        :return: string
        """
        self.ensure_one()
        acquirer = self.acquirer_id
        return acquirer.filtered(
            lambda a: a.provider == "adyen"
        ).adyen_merchant_account

    def _prepare_adyen_payments_request(self, payment_method):
        """
        https://docs.adyen.com/checkout/drop-in-web#step-3-make-a-payment
        Prepare payments request
        :param payment_method:
        :return:
        """
        currency = self.currency_id
        amount = self.amount
        request = {
            "merchantAccount": self._get_adyen_merchant_account(),
            "countryCode": self.partner_country_id.code,
            "reference": self.reference,
            "amount": {
                "value": self.env["invader.payable"]._get_formatted_amount(
                    self, amount
                ),
                "currency": currency.name,
            },
            "channel": "Web",
            "paymentMethod": payment_method,
            "returnUrl": self.return_url,
            "additionalData": {"executeThreeD": True},
        }
        return request

    def _get_adyen_service(self):
        """
        Return an intialized library
        :return:
        """
        adyen = Adyen.Adyen(
            platform=self._get_platform(),
            live_endpoint_prefix=self._get_live_prefix(),
            xapikey=self._get_adyen_api_key(),
        )
        return adyen

    def _get_live_prefix(self):
        state = self.acquirer_id.state
        prefix = self.acquirer_id.adyen_live_endpoint_prefix
        return str(prefix) if state == "enabled" else ""

    def _get_adyen_api_key(self):
        """
        Return adyen api key depending on payment.transaction recordset
        :return: string
        """

        acquirer = self.acquirer_id
        return acquirer.filtered(lambda a: a.provider == "adyen").adyen_api_key

    def _update_additional_details(self, response):
        """
        Hook to be able to enrich transaction with response
        additionalData
        :param vals:
        :param response:
        :return:
        """
        res = {}
        if response.message.get("action", {}).get("paymentMethodType"):
            payment_method = response.message.get("action", {}).get(
                "paymentMethodType"
            )
            res.update({"adyen_payment_method": payment_method})
        if response.message.get("paymentMethod", {}).get("type"):
            payment_method = response.message.get("paymentMethod", {}).get(
                "type"
            )
            res.update({"adyen_payment_method": payment_method})
        if response.message.get("paymentMethod", {}).get("brand"):
            payment_method = response.message.get("paymentMethod", {}).get(
                "brand"
            )
            res.update({"adyen_payment_method": payment_method})
        return res

    def _update_with_adyen_response(self, response):
        """
        Update the transaction with Adyen response
        :param response: AdyenResult
        :return:
        """
        vals = {}
        vals.update(self._update_additional_details(response))
        payment_data = response.message.get("paymentData")
        if payment_data:
            vals.update({"adyen_payment_data": payment_data})
        # In some strange case, we doesn't have this pspReference
        psp_reference = response.message.get("pspReference") or response.psp
        if psp_reference:
            vals.update({"acquirer_reference": psp_reference})
        result_code = response.message.get("resultCode")
        if result_code:
            # Log resultCode of Adyen in transaction
            message = self.state_message
            stamp = fields.Datetime.to_string(fields.Datetime.now())
            adyen_message = "\n" + stamp + ": " + str(response.message)
            if message:
                message += adyen_message
            else:
                message = adyen_message
            vals.update({"state_message": message})
        self.update(vals)
