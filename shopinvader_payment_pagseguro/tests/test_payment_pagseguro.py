# Copyright 2023 KMEE INFORMATICA LTDA (http://www.kmee.com.br).
# @author Cristiano Rodrigues <cristiano.rodrigues@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from vcr_unittest import VCRMixin

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderPagseguroPaymentCase(VCRMixin, CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderPagseguroPaymentCase, self).setUp(*args, **kwargs)
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_pagseguro")

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "one",
            "match_on": ["method", "path", "query"],
            "filter_headers": [
                "Authorization",
                "API_KEY",
                "PARTNER_EMAIL",
                "SESS-CART-ID",
            ],
            "decode_compressed_response": True,
        }

    def test_payment_pagseguro_credit_success(self):
        res = self.payment_service.dispatch(
            "confirm_payment_credit",
            params={
                "target": "current_cart",
                "card": {
                    "name": "SO0043",
                    "brand": "VISA",
                    "token": "Zq5ImQXUnZxn6...",
                    "installments": 1,
                },
            },
        )
        transaction = self.cart.transaction_ids
        self.assertEqual(len(transaction), 1)
        self.assertEqual(1, len(transaction))
        self.assertEqual("authorized", res.get("transaction_status"))

    def test_payment_pagseguro_credit_failed(self):
        res = self.payment_service.dispatch(
            "confirm_payment_credit",
            params={
                "target": "current_cart",
                "card": {
                    "name": "SO00179",
                    "brand": "VISA",
                    "token": "VaseeE7rr...",
                    "installments": 1,
                },
            },
        )
        self.assertEqual("draft", res.get("transaction_status"))
