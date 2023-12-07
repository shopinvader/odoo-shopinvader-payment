# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# If you change it, you have to create a migration script
ADYEN_PROVIDER = "adyen_web_dropin"


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[(ADYEN_PROVIDER, "Adyen Web drop-in")],
        ondelete={ADYEN_PROVIDER: "set default"},
    )
    adyen_dropin_api_key = fields.Char(
        groups="base.group_user", required_if_provider=ADYEN_PROVIDER
    )
    adyen_dropin_live_endpoint_prefix = fields.Char(
        groups="base.group_user",
        help="You need to fill this in when switching to live environment. "
        "See: https://docs.adyen.com/development-resources/"
        "live-endpoints#set-up-live-endpoints",
    )
    adyen_dropin_merchant_account = fields.Char(
        "Merchant Account",
        required_if_provider=ADYEN_PROVIDER,
        groups="base.group_user",
    )
    adyen_dropin_webhook_hmac = fields.Char(
        string="Adyen webhook HMAC",
        help="HMAC signature to ensure the webhook is provided by Adyen.\n"
        "Let this field empty to ignore signature (not recommended).\n"
        "Doc: https://docs.adyen.com/development-resources/webhooks/"
        "verify-hmac-signatures/#enable-hmac-signatures",
    )

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res["authorize"].append(ADYEN_PROVIDER)
        return res

    @api.onchange("provider")
    def _onchange_provider_adyen_web_dropin(self):
        if self.provider == ADYEN_PROVIDER:
            default = "?transaction_id={transaction.acquirer_reference}"
            self.return_url_suffix = default

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
