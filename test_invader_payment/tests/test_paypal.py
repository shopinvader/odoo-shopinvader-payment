# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os

from odoo import _
from odoo.exceptions import UserError
from vcr_unittest import VCRMixin

from .common import TestCommonPayment

_logger = logging.getLogger(__name__)

SUCCESS_REDIRECT = "/cart/validation"
CANCEL_REDIRECT = "/cart/checkout?canceled_payment=paypal"

NORMAL_RETURN_URL = (
    "https://shopinvader.com/invader/payment_paypal/normal_return?"
    "success_redirect={}&cancel_redirect={}"
).format(SUCCESS_REDIRECT, CANCEL_REDIRECT)

CANCEL_URL = "https://shopinvader.com/cart/checkout"

PAYPAL_FORM_PAGE = "https://www.sandbox.paypal.com/checkoutnow?token="


class TestInvaderPaymentPaypal(VCRMixin, TestCommonPayment):
    def setUp(self):
        super().setUp()
        self.payment_mode = self.env.ref(
            "invader_payment_paypal.payment_mode_paypal"
        )
        self.acquirer = self.env.ref("payment.payment_acquirer_paypal")
        self.acquirer.write(
            {
                "paypal_client_id": os.environ.get("PAYPAL_CLIENT_ID", "FAKE"),
                "paypal_secret": os.environ.get("PAYPAL_SECRET", "FAKE"),
            }
        )
        self.paypal_service = self._get_service("payment_paypal")

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": os.environ.get("PAYPAL_VCR_MODE", "none"),
            "match_on": ["method", "path", "query"],
            "filter_headers": ["Authorization"],
            "decode_compressed_response": True,
        }

    def _checkout_order(self):
        result = self.paypal_service.dispatch(
            "checkout_order",
            params={
                "target": "demo_partner",
                "payment_mode_id": self.payment_mode.id,
                "return_url": NORMAL_RETURN_URL,
                "cancel_url": CANCEL_URL,
            },
        )
        self.assertIn("redirect_to", result)
        self.assertIn(PAYPAL_FORM_PAGE, result["redirect_to"])
        token = result["redirect_to"].replace(PAYPAL_FORM_PAGE, "")
        return result["redirect_to"], token

    def _normal_return(self, token):
        return self.paypal_service.dispatch(
            "normal_return",
            params={
                "target": "demo_partner",
                "token": token,
                "success_redirect": SUCCESS_REDIRECT,
                "cancel_redirect": CANCEL_REDIRECT,
            },
        )

    def test_full_payment(self):
        form_url, token = self._checkout_order()
        if os.environ.get("PAYPAL_INTERACTIVE"):
            print("Running in interactive mode")
            print("Please fill the form at {}".format(form_url))
            input("Press Enter to continue...")

        result = self._normal_return(token)
        self.assertIn("redirect_to", result)
        self.assertEqual(result["redirect_to"], SUCCESS_REDIRECT)
        transaction = self.env["payment.transaction"].search(
            [("acquirer_reference", "=", token)]
        )
        self.assertEqual(transaction.state, "done")

    def test_wrong_api_key(self):
        self.acquirer.write({"paypal_secret": "WRONG"})
        with self.assertRaises(UserError) as m:
            self.paypal_service._get_api_token(self.acquirer)
        self.assertEqual(m.exception.name, _("Invalid Paypal Credential"))

    def test_full_failling_payment(self):
        form_url, token = self._checkout_order()
        # After redirecting the customer we do not fill
        # the paypal form manually so the payment capture
        # will fail and return to error page
        result = self._normal_return(token)
        self.assertIn("redirect_to", result)
        self.assertEqual(result["redirect_to"], CANCEL_REDIRECT)
        transaction = self.env["payment.transaction"].search(
            [("acquirer_reference", "=", token)]
        )
        self.assertEqual(transaction.state, "error")
