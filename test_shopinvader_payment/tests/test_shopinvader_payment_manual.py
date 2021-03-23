# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class TestShopinvaderPaymentManual(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.shopinvader_payment = self.env.ref(
            "shopinvader_payment_manual.shopinvader_payment_check"
        )
        self.account_payment_mode = self.shopinvader_payment.payment_mode_id
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_manual")

    def test_get_cart_payment_info(self):
        response = self.service.dispatch("search")
        self.assertIn("available_methods", response["data"]["payment"])
        self.assertEqual(
            response["data"]["payment"]["available_methods"]["count"],
            len(self.backend.payment_method_ids),
        )

    def test_add_check_payment(self):
        self.assertEqual(self.cart.typology, "cart")
        self.payment_service.dispatch(
            "add_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.account_payment_mode.id,
            },
        )
        self.assertEqual(self.cart.payment_mode_id, self.account_payment_mode)
        self.assertEqual(self.cart.typology, "sale")

    def test_no_check_payment(self):
        self.assertEqual(self.cart.typology, "cart")
        self.shopinvader_payment.unlink()
        with self.assertRaises(UserError):
            self.payment_service.dispatch(
                "add_payment",
                params={
                    "target": "current_cart",
                    "payment_mode_id": self.account_payment_mode.id,
                },
            )
        self.assertEqual(self.cart.typology, "cart")
