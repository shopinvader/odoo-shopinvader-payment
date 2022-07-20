# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from vcr_unittest import VCRMixin

from .common import TestCommonPayment

# This is a public key not linked to any account (stripe doc)
# use your own key if you want to debug from stripe dashboard
stripe_secret_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


class TestInvaderPaymentStripe(VCRMixin, TestCommonPayment):
    def setUp(self):
        super().setUp()
        acquirer = self.env.ref("payment.payment_acquirer_stripe")
        acquirer.write({"stripe_secret_key": stripe_secret_key})
        self.service = self._get_service("payment_stripe")
        self.demo_partner = self.env.ref("base.res_partner_1")

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "once",
            "match_on": ["method", "path", "query"],
            "filter_headers": ["Authorization"],
            "decode_compressed_response": True,
        }

    def _alter_next_response(self, data):
        next_response = self.cassette.responses[self.cassette.play_count]
        body_string = next_response["body"]["string"]
        body = json.loads(body_string.decode("utf-8"))
        body.update(data)
        next_response["body"]["string"] = json.dumps(body).encode("utf-8")

    def test_confirm_payment_one_step(self):
        result = self.service.dispatch(
            "confirm_payment",
            params={
                "target": "demo_partner",
                "stripe_payment_method_id": "pm_card_visa",
            },
        )
        self.assertEqual(result, {"success": True})

    def test_confirm_payment_two_step(self):
        result = self.service.dispatch(
            "confirm_payment",
            params={
                "target": "demo_partner",
                "stripe_payment_method_id": "pm_card_threeDSecure2Required",
            },
        )
        self.assertIn("requires_action", result)
        self.assertTrue(result["requires_action"])
        self.assertIn("payment_intent_client_secret", result)

        stripe_payment_intent_id = result["payment_intent_client_secret"].split(
            "_secret"
        )[0]

        # Complete step 2
        # it's seem that there is not way to process the action
        # on server side so the simpliest solution is to
        # hack the next response
        self._alter_next_response({"status": "succeeded"})
        result = self.service.dispatch(
            "confirm_payment",
            params={
                "target": "demo_partner",
                "stripe_payment_intent_id": stripe_payment_intent_id,
            },
        )
        self.assertEqual(result, {"success": True})
