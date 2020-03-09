# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class TestShopinvaderPaymentStripe(CommonConnectedCartCase):
    def test_two_steps_payment(self):
        self.payment_mode = self.env.ref(
            "invader_payment_stripe.payment_mode_stripe"
        )
        self.payment_mode.payment_acquirer_id.capture_manually = True
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_stripe_service = work.component(
                usage="payment_stripe"
            )
        result = self.payment_stripe_service.dispatch(
            "confirm_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.payment_mode.id,
                "stripe_payment_method_id": "pm_card_visa",
            },
        )
        self.assertEqual(result.get("success"), True, result)
        transactions = self.cart.authorized_transaction_ids
        self.assertEqual(len(transactions) > 0, True)
        transactions.action_capture()
        for transaction in transactions:
            self.assertEqual(transaction.state, "done")

    def test_one_step_payment(self):
        self.payment_mode = self.env.ref(
            "invader_payment_stripe.payment_mode_stripe"
        )
        self.payment_mode.payment_acquirer_id.capture_manually = False
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_stripe_service = work.component(
                usage="payment_stripe"
            )
        result = self.payment_stripe_service.dispatch(
            "confirm_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.payment_mode.id,
                "stripe_payment_method_id": "pm_card_visa",
            },
        )
        self.assertEqual(result.get("success"), True, result)
        transactions = self.cart.transaction_ids
        self.assertEqual(len(transactions) > 0, True)
        for transaction in transactions:
            self.assertEqual(transaction.state, "done")
