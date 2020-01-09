# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderManualPaymentCase(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderManualPaymentCase, self).setUp(*args, **kwargs)
        self.acquirer = self.env.ref("payment.payment_acquirer_transfer")

    @classmethod
    def setUpClass(cls):
        super(ShopinvaderManualPaymentCase, cls).setUpClass()
        cls.cart = cls.env.ref("shopinvader.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}
        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")
            cls.payment_service = work.component(usage="payment_manual")

    def test_payment_manual_service(self):
        self.assertFalse(self.cart.transaction_ids)
        self.payment_service.dispatch(
            "add_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.acquirer.id,
            },
        )
        self.assertEquals(1, len(self.cart.transaction_ids))
        self.assertEquals("pending", self.cart.transaction_ids.state)
