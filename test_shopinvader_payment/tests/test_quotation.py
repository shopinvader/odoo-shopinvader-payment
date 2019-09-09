# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase
from odoo.addons.shopinvader_quotation.tests.test_quotation import (
    CommonConnectedQuotationCase,
)
from odoo.exceptions import UserError


class ShopinvaderCartNoPaymentCase(CommonConnectedCartCase):
    def test_get_no_cart_payment_info(self):
        self.cart.order_line[0].product_id.only_quotation = True
        response = self.service.dispatch("search")
        self.assertEqual(
            response["data"]["payment"]["available_methods"]["count"], 0
        )


class ShopinvaderQuotationPaymentCase(CommonConnectedQuotationCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderQuotationPaymentCase, self).setUp(*args, **kwargs)
        self.payment_mode = self.env.ref(
            "shopinvader_payment_manual.shopinvader_payment_check"
        ).payment_mode_id
        with self.work_on_services(
            partner=self.partner, shopinvader_session=self.shopinvader_session
        ) as work:
            self.payment_service = work.component(usage="payment_manual")

    def test_get_cart_payment_info(self):
        self.quotation.order_line[0].product_id.only_quotation = True
        response = self.service.dispatch(
            "search", params={"id": self.quotation.id}
        )
        self.assertIn("available_methods", response["data"][0]["payment"])
        self.assertEqual(
            response["data"][0]["payment"]["available_methods"]["count"],
            len(self.backend.payment_method_ids),
        )

    def test_wrong_state_payment(self):
        self.assertEqual(self.quotation.typology, "quotation")
        with self.assertRaises(UserError):
            self.payment_service.dispatch(
                "add_payment",
                params={
                    "target": "quotation",
                    "quotation_id": self.quotation.id,
                    "payment_mode": self.payment_mode.id,
                },
            )
        self.assertEqual(self.quotation.typology, "quotation")

    def test_add_check_payment(self):
        self.assertEqual(self.quotation.typology, "quotation")
        self.quotation.state = "sent"
        self.payment_service.dispatch(
            "add_payment",
            params={
                "target": "quotation",
                "quotation_id": self.quotation.id,
                "payment_mode": self.payment_mode.id,
            },
        )
        self.assertEqual(self.quotation.typology, "sale")
