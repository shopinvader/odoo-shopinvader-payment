# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.shopinvader_restapi.tests.test_cart import CommonConnectedCartCase


class ShopinvaderPaymentCase(CommonConnectedCartCase):
    @classmethod
    def setUpClass(cls):
        super(ShopinvaderPaymentCase, cls).setUpClass()
        cls.cart = cls.env.ref("shopinvader_restapi.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}

        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")

    def _set_transaction(self):
        self.transaction = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.fake_payment.acquirer_id.id,
                "amount": self.cart.amount_total,
                "currency_id": self.cart.currency_id.id,
                "sale_order_ids": [(6, 0, self.cart.ids)],
            }
        )

    def _setup_payment_acquirer(self):
        vals = {"name": "Fake Acquirer", "provider": "manual"}
        acquirer_id = self.env["payment.acquirer"].create(vals)
        vals = {"acquirer_id": acquirer_id.id, "backend_id": self.backend.id}
        self.fake_payment = self.env["shopinvader.payment"].create(vals)

    def test_no_acquirer(self):
        response = self.cart_service.dispatch(
            "search", params={"id": self.cart.id}
        )
        self.assertEqual(
            0,
            response.get("data")
            .get("payment")
            .get("available_methods")
            .get("count"),
        )

    def test_acquirer(self):
        self._setup_payment_acquirer()
        response = self.cart_service.dispatch(
            "search", params={"id": self.cart.id}
        )
        self.assertEqual(
            1,
            response.get("data")
            .get("payment")
            .get("available_methods")
            .get("count"),
        )
        items = (
            response.get("data")
            .get("payment")
            .get("available_methods")
            .get("items")
        )
        self.assertEqual(1, len(items))
        self.assertEqual("Fake Acquirer", items[0].get("name"))

    def test_transactions(self):
        self._setup_payment_acquirer()
        self._set_transaction()

        response = self.cart_service.dispatch(
            "search", params={"id": self.cart.id}
        )
        transactions = response.get("data").get("transactions")
        transaction = transactions[0]
        self.assertEqual("draft", transaction.get("state"))
