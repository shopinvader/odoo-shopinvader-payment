# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderPaymentCase(CommonConnectedCartCase):
    def setUp(self):
        super().setUp()
        # TODO: This should be in setUpClass, but it needs to be changed
        #       in CommonConnectedCartCase first.
        self.acquirer_a, self.acquirer_b = self.env["payment.acquirer"].create(
            [
                {"name": "Fake Acquirer A", "provider": "manual"},
                {"name": "Fake Acquirer B", "provider": "manual"},
            ]
        )
        self.payment_a, self.payment_b = self.env["shopinvader.payment"].create(
            [
                {
                    "acquirer_id": self.acquirer_a.id,
                    "backend_id": self.backend.id,
                },
                {
                    "acquirer_id": self.acquirer_b.id,
                    "backend_id": self.backend.id,
                    "domain": "[('partner_invoice_id.country_id.code', '=', 'FR')]",
                },
            ]
        )

    def test_acquirer_available(self):
        self.cart.partner_invoice_id.country_id = self.env.ref("base.fr")
        data = self.service.dispatch("search", params={"id": self.cart.id})["data"]
        available_method_ids = {
            p["id"] for p in data["payment"]["available_methods"]["items"]
        }
        self.assertEqual(
            available_method_ids,
            set((self.acquirer_a | self.acquirer_b).ids),
            "Both payment methods should be available",
        )

    def test_acquirer_filtered_out(self):
        self.cart.partner_invoice_id.country_id = self.env.ref("base.ch")
        data = self.service.dispatch("search", params={"id": self.cart.id})["data"]
        available_method_ids = {
            p["id"] for p in data["payment"]["available_methods"]["items"]
        }
        self.assertEqual(
            available_method_ids,
            set(self.acquirer_a.ids),
            "Second payment method should be filtered out, country doesn't match",
        )
