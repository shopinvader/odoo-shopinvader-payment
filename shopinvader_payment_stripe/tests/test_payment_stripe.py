# Copyright 2020 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta

import mock
from odoo.addons.invader_payment_stripe.services.payment_stripe import (
    PaymentServiceStripe,
)
from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase
from stripe import PaymentIntent


class ShopinvaderStripePaymentCase(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderStripePaymentCase, self).setUp(*args, **kwargs)
        self.acquirer = self.env.ref("payment.payment_acquirer_stripe")

    @classmethod
    def setUpClass(cls):
        super(ShopinvaderStripePaymentCase, cls).setUpClass()
        cls.cart = cls.env.ref("shopinvader.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}
        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")
            cls.payment_service = work.component(usage="payment_stripe")

    def test_payment_stripe_service_succeeded(self):
        # Prepare a fake Stripe Intent
        # Call service
        # Check transaction state
        self.assertFalse(self.cart.transaction_ids)
        with mock.patch.object(
            PaymentServiceStripe, "_prepare_stripe_intent"
        ) as mock_service:
            intent = PaymentIntent(id="test_response")
            intent.status = "succeeded"
            mock_service.return_value = intent
            self.payment_service.dispatch(
                "confirm_payment",
                params={
                    "target": "current_cart",
                    "payment_mode_id": self.acquirer.id,
                    "stripe_payment_method_id": "pm_123456789",
                },
            )
        self.assertEquals(1, len(self.cart.transaction_ids))
        self.assertEquals("done", self.cart.transaction_ids.state)
        self.assertEquals(
            "test_response", self.cart.transaction_ids.acquirer_reference
        )
        # Simulating automatic confirmation cron (The transaction has to
        # be done for 10 minutes at least)
        self.cart.transaction_ids.write(
            {"date": datetime.now() - timedelta(minutes=10)}
        )
        self.env["payment.transaction"]._cron_post_process_after_done()
        self.assertEquals("sale", self.cart.state)
