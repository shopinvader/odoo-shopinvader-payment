# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from Adyen import AdyenAPIValidationError
from Adyen.util import is_valid_hmac_notification

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression

from .payment_acquirer import ADYEN_PROVIDER

_logger = logging.getLogger(__name__)
try:
    import Adyen
except ImportError as err:
    _logger.debug(err)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    adyen_payment_method = fields.Char()

    def _get_platform(self):
        """
        For Adyen: return 'test' or 'live' depending on acquirer value
        :return: str
        """
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            state = self.acquirer_id.state
            return "test" if state in ("disabled", "test") else "live"
        return super()._get_platform()

    def _get_adyen_merchant_account(self):
        return (
            self._get_adyen_dropin_merchant_account()
            or super()._get_adyen_merchant_account()
        )

    def _get_adyen_dropin_merchant_account(self):
        """
        Return adyen merchant account depending on
        payment.transaction recordset
        :return: string
        """
        self.ensure_one()
        acquirer = self.acquirer_id
        return acquirer.filtered(
            lambda a: a.provider == ADYEN_PROVIDER
        ).adyen_dropin_merchant_account

    def _get_service(self):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._get_adyen_web_dropin_service()
        return super()._get_service()

    def _trigger_transaction_provider(self, data):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._trigger_transaction_adyen_dropin(data)
        return super()._trigger_transaction_provider(data)

    def _prepare_transaction_data(self):
        res = super()._prepare_transaction_data()
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            res.update(self._prepare_adyen_dropin_session())
        return res

    def _trigger_transaction_adyen_dropin(self, data):
        adyen = self._get_service()
        try:
            response = adyen.checkout.sessions(data)
        except AdyenAPIValidationError as adyen_exception:
            self._update_with_error(adyen_exception)
            return {}
        else:
            return response

    def _trigger_transaction_adyen_dropin_payments(self, data):
        adyen = self._get_service()
        try:
            response = adyen.checkout.payments(data)
        except AdyenAPIValidationError as adyen_exception:
            self._update_with_error(adyen_exception)
            return {}
        else:
            return response

    def _partner_info_adyen_dropin(self, partner):
        """
        All of these keys are required for Adyen Klarna.
        It's not the goal of Odoo to do the check.
        And if Adyen change some requirements, we don't have
        to do an update of this module.
        """
        values = {
            "city": partner.city or "",
            "country": partner.country_id.code or "",
            "houseNumberOrName": "",
            "postalCode": partner.zip or "",
            "street": partner.street or "",
        }
        return values

    def _prepare_adyen_dropin_session(self):
        # Data are the same as the session
        # https://docs.adyen.com/api-explorer/Checkout/71/post/sessions
        data = self._prepare_adyen_session()
        payable = fields.first(self._get_invader_payables())
        partner = self.partner_id
        company = payable.company_id
        company_data = {"name": company.name}
        if company.website:
            company_data.update({"homepage": company.website})
        data.update(
            {
                "returnUrl": self.return_url,
                "company": company_data,
                "channel": "Web",
                "shopperReference": payable._get_internal_ref(),
                "billingAddress": self._partner_info_adyen_dropin(
                    payable._get_billing_partner()
                ),
                "deliveryAddress": self._partner_info_adyen_dropin(
                    payable._get_delivery_partner()
                ),
                "lineItems": [
                    payable._prepare_payment_line(self, line)
                    for line in payable._get_payable_lines()
                ],
            }
        )
        if partner.phone:
            data.update({"telephoneNumber": partner.phone})
        # Could not exist in test mode
        # Commented because behind locomotive, it's his URL instead of the real user.
        # try:
        #     if request.httprequest.environ.get("REMOTE_ADDR"):
        #         data.update(
        #             {
        #                 "shopperIP": request.httprequest.environ.get(
        #                     "REMOTE_ADDR"
        #                 )
        #             }
        #         )
        # except RuntimeError:
        #     pass
        return data

    def _update_with_error(self, adyen_exception):
        # values = {
        #     "acquirer_reference": response.message.get('id'),
        # }
        # self.write(values)
        self._set_transaction_error(adyen_exception.message)
        return True

    def _update_with_response(self, response):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._update_with_response_adyen_dropin(response)
        return super()._update_with_response(response)

    def _parse_transaction_response(self, response):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._parse_transaction_response_adyen_dropin(response)
        return super()._parse_transaction_response(response)

    def _parse_transaction_response_adyen_dropin(self, response):
        return response

    def _update_with_response_adyen_dropin(self, response):
        """
        Based on the given Adyen response (after checkout.sessions(...)),
        update the current transaction and set it in pending state.
        Example of Adyen response:
        https://docs.adyen.com/online-payments/build-your-integration/
        ?platform=Web&integration=Drop-in&version=5.55.1#sessions-response-web
        {
            "amount": {
                "currency": "EUR",
                "value": 1000
            },
            "countryCode": "NL",
            "expiresAt": "2021-08-24T13:35:16+02:00",
            "id": "CSD9CAC34EBAE225DD",
            "merchantAccount": "YOUR_MERCHANT_ACCOUNT",
            "reference": "YOUR_PAYMENT_REFERENCE",
            "returnUrl": "https://your-company.com/checkout?shopperOrder=12xy..",
            "sessionData": "Ab02b4c.."
        }
        return: bool
        """
        if not hasattr(response, "message"):
            raise exceptions.ValidationError(
                _("Missing message from Adyen web-dropin response")
            )
        if not response.message.get("id"):
            raise exceptions.ValidationError(
                _("Missing session ID from Adyen web-dropin response")
            )
        if not hasattr(response, "status_code"):
            # https://docs.adyen.com/development-resources/error-codes/
            raise exceptions.ValidationError(
                _("Missing session status_code from Adyen web-dropin response")
            )
        # TODO: Even if the status code is not valid,
        # we should save some data into the transaction
        if response.status_code != 201:
            # https://docs.adyen.com/development-resources/error-codes/
            raise exceptions.ValidationError(
                _(
                    "Invalid status code from Adyen (expected 201; receive {code})"
                ).format(code=response.status_code)
            )
        values = {
            "acquirer_reference": response.message.get("id"),
        }
        self.write(values)
        self._set_transaction_pending()
        return True

    def _get_adyen_web_dropin_service(self):
        """
        Return an intialized library
        :return:
        """
        adyen = Adyen.Adyen(
            platform=self._get_platform(),
            live_endpoint_prefix=self._get_live_prefix(),
            xapikey=self._get_adyen_dropin_api_key(),
        )
        return adyen

    def _get_live_prefix(self):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            state = self.acquirer_id.state
            prefix = self.acquirer_id.adyen_dropin_live_endpoint_prefix
            return str(prefix) if state == "enabled" else ""
        return super()._get_live_prefix()

    def _get_adyen_dropin_api_key(self):
        """
        Return adyen api key depending on payment.transaction recordset
        :return: string
        """
        return self.acquirer_id.filtered(
            lambda a: a.provider == ADYEN_PROVIDER
        ).adyen_dropin_api_key

    @api.model
    def manage_adyen_dropin_webhook(self, response, queue_job=False):
        """
        {
            "live": "false",  # Determine if test or live (prod) env
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "eventCode": "AUTHORISATION",
                        "merchantAccountCode": "YOUR_MERCHANT_ACCOUNT",
                        "reason": "033899:1111:03/2030",
                        "amount": {
                            "currency":"EUR",
                            "value":2500
                        },
                        "operations": ["CANCEL", "CAPTURE", "REFUND"],
                        "success": "true",  # This define if the payment is ok
                        "paymentMethod": "mc",
                        # https://docs.adyen.com/development-resources/
                        # webhooks/additional-settings/
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": "CSF46729982237A879"
                        },
                        "merchantReference": "YOUR_REFERENCE",
                        "pspReference": "NC6HT9CRT65ZGN82",
                        "eventDate": "2021-09-13T14:10:22+02:00",
                    }
                }
            ]
        }
        """
        try:
            for notification_item in response.get("notificationItems", []):
                notif_request_item = notification_item.get(
                    "NotificationRequestItem", {}
                )
                reference = notif_request_item.get("additionalData", {}).get(
                    "checkoutSessionId"
                )
                odoo_ref = notif_request_item.get("merchantReference")
                # domain = [("acquirer_reference", "=", notif_request_item.get("pspReference"))]
                domain = [("acquirer_reference", "=", reference)]
                if odoo_ref:
                    domain = expression.OR(
                        [domain, [("reference", "=", odoo_ref)]]
                    )
                domain = expression.AND(
                    [[("acquirer_id.provider", "=", ADYEN_PROVIDER)], domain]
                )
                transaction = self.search(domain, limit=1)
                if not transaction:
                    _logger.error("Session %s not found!" % reference)
                    raise ValueError("Session %s not found!" % reference)
                if queue_job:
                    transaction.with_delay(
                        description="Adyen web-dropin - Webhook",
                        channel="root.adyen_dropin",
                    )._manage_notif_item(notif_request_item)
                else:
                    transaction._manage_notif_item(notif_request_item)
            return "[accepted]"
        except Exception as e:
            _logger.error("Error during Adyen web-dropin webhook: %s" % e)
            return "[error]"

    def _manage_notif_item(self, notification_item):
        self.ensure_one()
        acquirer = self.acquirer_id
        adyen_ref = self.acquirer_reference
        if acquirer.provider != ADYEN_PROVIDER:
            message = _(
                "Transaction with reference '%s' has wrong provider "
                "in Adyen automatic response" % adyen_ref
            )
            _logger.warning(message)
            raise exceptions.ValidationError(message)
        event_code = notification_item.get("eventCode")
        success = notification_item.get("success") == "true"
        # Give a copy because this check drop the "additionalData" key.
        if not is_valid_hmac_notification(
            notification_item.copy(),
            self.acquirer_id.adyen_dropin_webhook_hmac,
        ):
            message = _("Transaction Data is not safe!")
            _logger.warning(message)
            raise exceptions.ValidationError(message)

        data = self._get_adyen_dropin_additional_data(notification_item)
        if data:
            self.write(data)
        # https://docs.adyen.com/development-resources/webhooks/webhook-types/#event-codes
        if event_code == "AUTHORISATION" and success:
            self._set_transaction_done()
            self._handle_adyen_notification_item_authorized(notification_item)
        elif event_code == "AUTHORISATION" and not success:
            self._handle_adyen_notification_item_capture_failed(
                notification_item
            )
        elif event_code == "REFUND":
            self._handle_adyen_notification_item_refund(notification_item)
        elif event_code == "CANCELLATION":
            self._handle_adyen_notification_item_cancel(notification_item)
        elif event_code == "CAPTURE":
            self._handle_adyen_notification_item_capture(notification_item)
        elif event_code == "CAPTURE_FAILED":
            self._handle_adyen_notification_item_capture_failed(
                notification_item
            )
        else:
            _logger.error("Not implemented event_code %s" % event_code)
            raise NotImplementedError(
                "Not implemented event_code %s" % event_code
            )
        self._notify_state_changed_event()

    def _get_adyen_dropin_additional_data(self, notification_item):
        """Allows to update transaction details with additional data
        comming from Adyen.

        :param notification_item: [description]
        :type notification_item: [type]
        """
        vals = {}
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            message = self._get_adyen_dropin_notification_message(
                notification_item
            )
            vals.update({"state_message": message})
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

    def _get_adyen_dropin_notification_message(self, notification_item):
        message = self.state_message
        notification_message = (
            "eventCode: {}, merchantReference: {}, sessionId: {}".format(
                notification_item.get("eventCode"),
                notification_item.get("merchantReference"),
                notification_item.get("additionalData", {}).get(
                    "checkoutSessionId"
                ),
            )
        )
        stamp = fields.Datetime.to_string(fields.Datetime.now())
        adyen_message = "\n" + stamp + ": " + str(notification_message)
        if message:
            message += adyen_message
        else:
            message = adyen_message
        return message
