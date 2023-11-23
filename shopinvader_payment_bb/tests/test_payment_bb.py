# Copyright 2023 KMEE INFORMATICA LTDA (http://www.kmee.com.br).
# @author Cristiano Rodrigues <cristiano.rodrigues@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from vcr_unittest import VCRMixin

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderBbPaymentCase(VCRMixin, CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderBbPaymentCase, self).setUp(*args, **kwargs)
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_bacen_pix")

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

    def test_payment_bb_success(self):
        self.payment_service.dispatch(
            "confirm_payment_pix",
            params={"target": "current_cart", "tx_id": "123456789"},
        )
        transaction = self.cart.transaction_ids
        self.assertEqual(len(transaction), 1)
        self.assertEqual("ATIVA", transaction.bacenpix_state)

    def test_payment_bb_failed(self):
        self.payment_service.dispatch(
            "confirm_payment_pix",
            params={"target": "current_cart", "tx_id": "12345678*"},
        )
        transaction = self.cart.transaction_ids
        self.assertEqual(len(transaction), 0)
        self.assertEqual(False, transaction.bacenpix_state)
