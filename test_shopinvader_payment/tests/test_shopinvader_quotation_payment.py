# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class TestShopinvaderQuotationPaymentCart(CommonConnectedCartCase):
    def test_get_no_cart_payment_info(self):
        """
        Data:
            A cart with a product requiring a quotation
        Test Case:
            Retrieve the cart info
        Expected result:
            'available_methods' must not have any payment mode as only
            a request_quotation is allowed
        """
        self.cart.order_line[0].product_id.only_quotation = True
        response = self.service.dispatch("search")
        self.assertEqual(
            response["data"]["payment"]["available_methods"]["count"], 0
        )


class TestShopinvaderQuotationPayment(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.quotation = self.env.ref("shopinvader.sale_order_2")
        self.quotation.action_request_quotation()
        self.payment_mode = self.env.ref(
            "invader_payment_manual.payment_mode_check"
        )
        with self.work_on_services(partner=self.partner) as work:
            self.payment_manual_service = work.component(
                usage="payment_manual"
            )
            self.quotation_service = work.component(usage="quotations")

    def _check_number_of_payment_mode(self, response, expected_number):
        self.assertIn("available_methods", response["data"][0]["payment"])
        self.assertEqual(
            response["data"][0]["payment"]["available_methods"]["count"],
            expected_number,
        )

    def test_quotation_payment_info_with_normal_product(self):
        """
        Data:
            A quotation
        Test Case:
            Retrieve the quotation info
        Expected result:
            'available_methods' must have all payment mode
        """
        response = self.quotation_service.dispatch(
            "search", params={"id": self.quotation.id}
        )
        self._check_number_of_payment_mode(
            response, len(self.backend.payment_method_ids)
        )

    def test_quotation_payment_info_with_required_quotation_product(self):
        """
        Data:
            A quotation with one product that required quotation
        Test Case:
            Retrieve the quotation info
        Expected result:
            'available_methods' must have all payment mode
        """
        self.quotation.order_line[0].product_id.only_quotation = True
        response = self.quotation_service.dispatch(
            "search", params={"id": self.quotation.id}
        )
        self._check_number_of_payment_mode(
            response, len(self.backend.payment_method_ids)
        )

    def test_can_not_pay_quotation_not_yet_estimated(self):
        with self.assertRaises(UserError) as m:
            self.payment_manual_service.dispatch(
                "add_payment",
                params={
                    "target": "quotation",
                    "quotation_id": self.quotation.id,
                    "payment_mode_id": self.payment_mode.id,
                },
            )
        self.assertEqual(self.quotation.typology, "quotation")
        self.assertEqual(
            m.exception.name, _("The quotation is not yet estimated")
        )

    def test_pay_quotation_with_check(self):
        self.quotation.state = "sent"
        self.payment_manual_service.dispatch(
            "add_payment",
            params={
                "target": "quotation",
                "quotation_id": self.quotation.id,
                "payment_mode_id": self.payment_mode.id,
            },
        )
        self.assertEqual(self.quotation.typology, "sale")
