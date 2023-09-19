# Copyright 2023 KMEE INFORMATICA LTDA (http://www.kmee.com.br).
# @author Cristiano Rodrigues <cristiano.rodrigues@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderListPaymentCase(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderListPaymentCase, self).setUp(*args, **kwargs)
        backend_one = self.env["shopinvader.backend"].search(
            [("name", "=", "Demo Shopinvader Website")]
        )
        backend_one.payment_method_ids.create(
            {"code": "PayPal", "acquirer_id": 8, "backend_id": 1}
        )
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_list_method")

    def test_list_payment_method_success(self):
        method_payment = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        method_payment.provider = "manual"
        res = self.payment_service.dispatch(
            "list_payment_method",
            params={},
        )

        self.assertEqual(len(res.get("list_payment_methods")), 1)
        self.assertGreaterEqual(
            len(res.get("list_payment_methods")[0]["method"]), 1
        )

    def test_list_payment_method_failed(self):
        res = self.payment_service.dispatch(
            "list_payment_method",
            params={},
        )

        self.assertEqual(len(res.get("list_payment_methods")[0]["method"]), 0)
