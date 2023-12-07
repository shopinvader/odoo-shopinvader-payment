# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from Adyen import AdyenAPIValidationError

from odoo import fields, models

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
        """
        Return adyen merchant account depending on
        payment.transaction recordset
        :return: string
        """
        self.ensure_one()
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self.acquirer_id.adyen_merchant_account
        return super()._get_adyen_merchant_account()

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
            "additionalData": {"executeThreeD": True},
        }
        if self.return_url:
            request.update({"returnUrl": self.return_url})
        return request

    def _trigger_transaction_provider(self, data):
        # In the best world, this function should be more abstract if call super
        # if not the expected provider.
        # if self.acquirer_id.provider == ADYEN_PROVIDER:
        self.ensure_one()
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._trigger_transaction_adyen(data)
        return super()._trigger_transaction_provider(data)

    def _prepare_transaction_data(self):
        res = super()._prepare_transaction_data()
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            res.update(self._prepare_adyen_session())
        return res

    def _trigger_transaction_adyen(self, data):
        adyen = self._get_service()
        try:
            response = adyen.checkout.payment_methods(data)
        except AdyenAPIValidationError as adyen_exception:
            self._update_with_error(adyen_exception)
            return {}
        else:
            self._update_with_response(response)
            return response

    def _get_service(self):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._get_adyen_service()
        return super()._get_service()

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
        if response.get("action", {}).get("paymentMethodType"):
            payment_method = response.get("action", {}).get(
                "paymentMethodType"
            )
            res.update({"adyen_payment_method": payment_method})
        if response.get("paymentMethod", {}).get("type"):
            payment_method = response.get("paymentMethod", {}).get("type")
            res.update({"adyen_payment_method": payment_method})
        if response.get("paymentMethod", {}).get("brand"):
            payment_method = response.get("paymentMethod", {}).get("brand")
            res.update({"adyen_payment_method": payment_method})
        return res

    def _update_with_response(self, response):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._update_with_adyen_response(response)
        return super()._update_with_response(response)

    def _parse_transaction_response(self, response):
        if self.acquirer_id.provider == ADYEN_PROVIDER:
            return self._parse_transaction_response_adyen(response)
        return super()._parse_transaction_response(response)

    def _parse_transaction_response_adyen(self, response):
        return response

    def _update_with_adyen_response(self, response):
        """
        Update the transaction with Adyen response
        :param response: AdyenResult
        :return:
        """
        response = response.message
        vals = {}
        vals.update(self._update_additional_details(response))
        payment_data = response.get("paymentData")
        if payment_data:
            vals.update({"adyen_payment_data": payment_data})
        # In some strange case, we doesn't have this pspReference
        psp_reference = response.get("pspReference") or getattr(
            response, "psp", ""
        )
        if psp_reference:
            vals.update({"acquirer_reference": psp_reference})
        result_code = response.get("resultCode")
        if result_code:
            # Log resultCode of Adyen in transaction
            message = self.state_message
            stamp = fields.Datetime.to_string(fields.Datetime.now())
            adyen_message = "\n" + stamp + ": " + str(response)
            if message:
                message += adyen_message
            else:
                message = adyen_message
            vals.update({"state_message": message})
        self.update(vals)
