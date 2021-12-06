# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.exceptions import UserError

from odoo.addons.shopinvader_payment.tests.common import CommonConnectedPaymentCase


class ShopinvaderManualPaymentCase(CommonConnectedPaymentCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.acquirer = self.env.ref("payment.payment_acquirer_transfer")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cart = cls.env.ref("shopinvader.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}
        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")
            cls.payment_service = work.component(usage="payment_manual")

    def test_payment_manual_service(self):
        self.assertFalse(self.cart.transaction_ids)
        with self._mock_request(self.shopinvader_session["cart_id"]):
            res = self.payment_service.dispatch(
                "add_payment",
                params={
                    "target": "current_cart",
                    "payment_mode_id": self.acquirer.id,
                },
            )
            self.assertEqual(1, len(self.cart.transaction_ids))
            self.assertEqual("pending", self.cart.transaction_ids.state)
            self.assertIn("store_cache", res)
            self.assertIn("cart", res["store_cache"])
            self.assertEqual(res["store_cache"]["cart"], {})
            self.assertIn("last_sale", res["store_cache"])
            self.assertEqual(
                res["store_cache"]["last_sale"]["id"], self.cart.id
            )

    def test_get_cart_payment_info(self):
        response = self.service.dispatch("search")
        self.assertIn("available_methods", response["data"]["payment"])
        self.assertEqual(
            response["data"]["payment"]["available_methods"]["count"],
            len(self.backend.payment_method_ids),
        )

    def test_no_congigured_payment(self):
        self.assertEqual(self.cart.typology, "cart")
        self.env.ref(
            "shopinvader_payment_manual.shopinvader_payment_banktransfer"
        ).unlink()
        with self.assertRaises(UserError):
            self.payment_service.dispatch(
                "add_payment",
                params={
                    "target": "current_cart",
                    "payment_mode_id": self.acquirer.id,
                },
            )
        self.assertEqual(self.cart.typology, "cart")
