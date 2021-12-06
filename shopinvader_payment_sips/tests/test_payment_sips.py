# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.invader_payment_sips.services.payment_sips import _sips_make_seal
from odoo.addons.shopinvader_payment.tests.common import CommonConnectedPaymentCase


class ShopinvaderSipsPaymentCase(CommonConnectedPaymentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acquirer = cls.env.ref("payment.payment_acquirer_sips")
        cls.acquirer.sips_secret = "foobarsecretkey"
        cls.cart = cls.env.ref("shopinvader.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}
        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")
            cls.payment_service = work.component(usage="payment_sips")

    def test_payment_sips_service(self):
        self.assertFalse(self.cart.transaction_ids)
        res = self.payment_service.dispatch(
            "prepare_payment",
            params={
                "normal_return_url": "https://example.org/normal",
                "automatic_response_url": "https://example.org/automatic",
                "target": "current_cart",
                "payment_mode_id": self.acquirer.id,
            },
        )
        self.assertEqual(1, len(self.cart.transaction_ids))
        self.assertEqual("draft", self.cart.transaction_ids.state)

        data = res["sips_data"] + "|responseCode=00"
        seal = _sips_make_seal(data, self.acquirer.sips_secret)

        with self._mock_request(self.shopinvader_session["cart_id"]):
            res = self.payment_service.dispatch(
                "normal_return",
                params={
                    "target": "current_cart",
                    "success_redirect": "https://example.org/success",
                    "cancel_redirect": "https://example.org/cancel",
                    "Data": data,
                    "Seal": seal,
                    "InterfaceVersion": "1",
                },
            )
            self.assertEqual(1, len(self.cart.transaction_ids))
            self.assertEqual("done", self.cart.transaction_ids.state)
            self.assertIn("store_cache", res)
            self.assertIn("cart", res["store_cache"])
            self.assertEqual(res["store_cache"]["cart"], {})
            self.assertIn("last_sale", res["store_cache"])
            self.assertEqual(res["store_cache"]["last_sale"]["id"], self.cart.id)
