# Copyright Odoo SA (https://odoo.com)
# Copyright 2024 ACSONE SA (https://acsone.eu).
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from urllib.parse import urljoin

from odoo import api, models


class PaymentTransactionSips(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _update_encoded_rendering_values(self, data, data_update):
        """

        :param data: rendering data encoded as follows: "a=1|b=2|c=3".
        :param data_update: dict containing data to update / add in rendering data
        :return: updated rendering data
        """
        data_list = data.split("|")
        data_dict = {}
        for data_elem in data_list:
            key, value = data_elem.split("=")
            data_dict[key] = value

        data_dict.update(data_update)
        updated_data = "|".join([f"{k}={v}" for k, v in data_dict.items()])
        return updated_data

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return Sips-specific rendering values.
        Update the Odoo url values, and then re-sign the response

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific
        processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        shopinvader_api_payment = self.env.context.get("shopinvader_api_payment")

        res = super()._get_specific_rendering_values(processing_values)

        if self.provider_code != "sips" or not shopinvader_api_payment:
            return res

        shopinvader_api_payment_frontend_redirect_url = (
            self.shopinvader_frontend_redirect_url
        )
        shopinvader_api_payment_base_url = self.env.context.get(
            "shopinvader_api_payment_base_url"
        )

        data_update = {
            "normalReturnUrl": urljoin(shopinvader_api_payment_base_url, "sips/return"),
            "automaticResponseUrl": urljoin(
                shopinvader_api_payment_base_url, "sips/webhook"
            ),
            "returnContext": json.dumps(
                dict(
                    reference=self.reference,
                    frontend_redirect_url=shopinvader_api_payment_frontend_redirect_url,
                )
            ),
        }
        res["Data"] = self._update_encoded_rendering_values(res["Data"], data_update)
        res["Seal"] = self.provider_id._sips_generate_shasign(res["Data"])
        return res
