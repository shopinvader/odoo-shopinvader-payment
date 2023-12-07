# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

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
    adyen_hmac_key = fields.Char(
        string="HMAC Key",
        help="The HMAC key of the webhook",
        groups="base.group_user",
    )
    delay_capture = fields.Boolean(
        help="In some case of Adyen payment, a delay capture is possible (Klarna)"
    )
