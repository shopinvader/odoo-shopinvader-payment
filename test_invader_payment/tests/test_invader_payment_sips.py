# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
from odoo import _
from odoo.exceptions import UserError
from vcr_unittest import VCRMixin

from .common import TestCommonPayment

MERCHAND_ID = "002001000000001"
SECRET_KEY = "002001000000001_KEY1"
KEY_VERSION = 1

NORMAL_RETURN_URL = (
    "https://shopinvader.com/invader/payment_sips/normal_return?"
    "success_redirect=/cart/validation"
    "&cancel_redirect=/cart/checkout?canceled_payment=sips"
    "&target=current_cart"
)

AUTOMATIC_RESPONSE_URL = (
    "https://shopinvader.com/invader/payment_sips/automatic_response"
)


class TestInvaderPaymentSips(VCRMixin, TestCommonPayment):
    def setUp(self):
        super(TestInvaderPaymentSips, self).setUp()
        self.payment_mode = self.env.ref(
            "invader_payment_sips.payment_mode_sips"
        )
        acquirer = self.env.ref("payment.payment_acquirer_sips")
        acquirer.write(
            {"sips_secret": SECRET_KEY, "sips_merchant_id": MERCHAND_ID}
        )
        self.env["ir.config_parameter"].set_param("sips.key_version", 1)
        self.service = self._get_service("payment_sips")

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "one",
            "match_on": ["method", "path", "query"],
            "filter_headers": [],
            "decode_compressed_response": True,
        }

    def test_prepare_payment(self):
        result = self.service.dispatch(
            "prepare_payment",
            params={
                "target": "demo_partner",
                "payment_mode_id": self.payment_mode.id,
                "normal_return_url": NORMAL_RETURN_URL,
                "automatic_response_url": AUTOMATIC_RESPONSE_URL,
            },
        )
        response = requests.post(
            result["sips_form_action_url"],
            params={
                "Data": result["sips_data"],
                "InterfaceVersion": result["sips_interface_version"],
                "Seal": result["sips_seal"],
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_wrong_provider_prepare_payment(self):
        self.payment_mode_check = self.env.ref(
            "invader_payment_manual.payment_mode_check"
        )
        with self.assertRaises(UserError) as m:
            self.service.dispatch(
                "prepare_payment",
                params={
                    "target": "demo_partner",
                    "payment_mode_id": self.payment_mode_check.id,
                    "normal_return_url": NORMAL_RETURN_URL,
                    "automatic_response_url": AUTOMATIC_RESPONSE_URL,
                },
            )
        self.assertEqual(
            m.exception.name,
            _(
                "Payment mode acquirer mismatch should be "
                "'sips' instead of 'transfer'."
            ),
        )
