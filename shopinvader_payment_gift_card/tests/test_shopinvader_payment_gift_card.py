# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions

from odoo.addons.datamodel.tests.common import SavepointDatamodelCase
from odoo.addons.gift_card.tests.common import TestGiftCardCommon
from odoo.addons.shopinvader.tests.test_sale import CommonSaleCase


class ShopinvaderPaymentGiftcardTest(
    CommonSaleCase,
    TestGiftCardCommon,
    SavepointDatamodelCase,
):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.gift_card_journal = self.env.ref("gift_card.gift_card_journal")
        self.cart = self.env.ref("shopinvader.sale_order_2")
        self.acquirer = self.env.ref("payment.payment_acquirer_transfer")
        self.acquirer.journal_id = self.env["account.journal"].search(
            [("code", "=", "BNK1")]
        )
        shopinvader_session = {"cart_id": self.cart.id}

        self.gc1 = self.env["gift.card"].create(
            {
                "initial_amount": 100,
                "is_divisible": True,
                "duration": 0,
                "buyer_id": self.cart.partner_id.id,
                "gift_card_tmpl_id": self.env.ref("gift_card.product_gift_card").id,
            }
        )

        with self.work_on_services(
            partner=None, shopinvader_session=shopinvader_session
        ) as work:
            self.cart_service = work.component(usage="cart")
            self.payment_service = work.component(usage="payment_manual")
            self.service_gift_card = work.component(usage="payment_gift_card")

    def test_1_get_gift_card_from_code(self):
        params = {
            "code": self.gc1.code,
        }
        response = self.cart_service.dispatch("get_gift_card_from_code", params=params)
        self.assertEqual(self.gc1.id, response[0].get("id"))

    def test_2_gift_card_amount_validation(self):
        self.gc1.beneficiary_id = self.cart.partner_id
        params = {"card": self.gc1, "gift_card_amount": 30.5, "code": self.gc1.code}
        response = self.cart_service.dispatch(
            "gift_card_amount_validation", params=params
        )
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)
        self.assertEqual(response[0].get("amount_used"), 30.5)
        self.assertEqual(self.cart.gift_card_line_ids[0].amount_used, 30.5)
        self.assertEqual(self.cart.remain_amount, self.cart.amount_total - 30.5)

    def test_3_payment_gift_card(self):
        self.assertFalse(self.cart.transaction_ids)
        params = {
            "card": self.gc1,
            "gift_card_amount": 45,
            "code": self.gc1.code,
        }
        self.cart_service.dispatch("gift_card_amount_validation", params=params)
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)

        self.assertEqual(0, len(self.cart.transaction_ids))
        self.assertEqual(self.cart.remain_amount, self.cart.amount_total - 45)

        self.payment_service.dispatch(
            "add_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.acquirer.id,
            },
        )

        self.assertEqual(1, len(self.cart.transaction_ids))
        self.assertEqual("pending", self.cart.transaction_ids.state)
        self.assertFalse(self.cart.transaction_ids.is_processed)
        self.assertEqual(self.cart.transaction_ids.amount, self.cart.remain_amount)

        self.cart.transaction_ids._post_process_after_done()
        self.assertEqual("sale", self.cart.state)
        self.assertEqual(2, len(self.cart.transaction_ids))
        self.assertEqual(2, len(self.cart.transaction_ids.payment_id))

        payment_manual, payment_gift_card = self.cart.transaction_ids.payment_id
        self.assertEqual(payment_manual.state, "posted")
        self.assertEqual(payment_manual.amount, self.cart.remain_amount)
        self.assertRecordValues(
            payment_manual.line_ids,
            [
                {
                    "journal_id": self.acquirer.journal_id.id,
                    "debit": self.cart.remain_amount,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.acquirer.journal_id.id,
                    "debit": 0.0,
                    "credit": self.cart.remain_amount,
                },
            ],
        )

        self.assertEqual(payment_gift_card.state, "posted")
        self.assertEqual(payment_gift_card.amount, 45.0)
        self.assertRecordValues(
            payment_gift_card.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 45.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 45.0,
                },
            ],
        )

    def test_4_payment_with_two_gift_cards(self):
        self.assertFalse(self.cart.transaction_ids)

        params = {
            "card": self.gc1,
            "gift_card_amount": 45,
            "code": self.gc1.code,
        }
        self.cart_service.dispatch("gift_card_amount_validation", params=params)

        self.assertEqual(0, len(self.cart.transaction_ids))
        self.assertEqual(self.cart.remain_amount, self.cart.amount_total - 45)

        params = {
            "card": self.gc2,
            "gift_card_amount": 30,
            "code": self.gc2.code,
        }
        self.cart_service.dispatch("gift_card_amount_validation", params=params)

        self.assertEqual(len(self.cart.gift_card_line_ids), 2)
        self.assertEqual(self.cart.remain_amount, self.cart.amount_total - 75)

        self.payment_service.dispatch(
            "add_payment",
            params={
                "target": "current_cart",
                "payment_mode_id": self.acquirer.id,
            },
        )

        self.assertEqual(1, len(self.cart.transaction_ids))
        self.assertEqual("pending", self.cart.transaction_ids.state)
        self.assertFalse(self.cart.transaction_ids.is_processed)
        self.assertEqual(self.cart.transaction_ids.amount, self.cart.remain_amount)

        self.cart.transaction_ids._post_process_after_done()
        self.assertEqual("sale", self.cart.state)
        self.assertEqual(3, len(self.cart.transaction_ids))
        self.assertEqual(3, len(self.cart.transaction_ids.payment_id))

        (
            payment_manual,
            payment_gift_card_1,
            payment_gift_card_2,
        ) = self.cart.transaction_ids.payment_id
        self.assertEqual(payment_manual.state, "posted")
        self.assertEqual(payment_manual.amount, self.cart.remain_amount)
        self.assertRecordValues(
            payment_manual.line_ids,
            [
                {
                    "journal_id": self.acquirer.journal_id.id,
                    "debit": self.cart.remain_amount,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.acquirer.journal_id.id,
                    "debit": 0.0,
                    "credit": self.cart.remain_amount,
                },
            ],
        )

        self.assertEqual(payment_gift_card_1.state, "posted")
        self.assertEqual(payment_gift_card_1.amount, 45.0)
        self.assertRecordValues(
            payment_gift_card_1.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 45.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 45.0,
                },
            ],
        )

        self.assertEqual(payment_gift_card_2.state, "posted")
        self.assertEqual(payment_gift_card_2.amount, 30.0)
        self.assertRecordValues(
            payment_gift_card_2.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 30.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 30.0,
                },
            ],
        )

    def test_5_unlink_gift_card_line(self):
        gc1_initial_amount = self.gc1.initial_amount
        params = {
            "card": self.gc1,
            "gift_card_amount": gc1_initial_amount,
            "code": self.gc1.code,
        }
        gift_card_line = self.cart_service.dispatch(
            "gift_card_amount_validation", params=params
        )
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)
        self.assertEqual(
            self.cart.remain_amount, self.cart.amount_total - gc1_initial_amount
        )
        self.gc1._update_soldout_state(self.gc1)
        self.assertEqual(self.gc1.state, "soldout")
        self.assertEqual(len(self.gc1.gift_card_line_ids), 1)

        params2 = {"line_id": gift_card_line[0].get("id")}
        self.cart_service.dispatch("unlink_gift_card_line", params=params2)
        self.assertEqual(len(self.cart.gift_card_line_ids), 0)
        self.assertEqual(self.cart.remain_amount, self.cart.amount_total)
        self.assertEqual(len(self.gc1.gift_card_line_ids), 0)
        self.assertEqual(self.gc1.state, "active")

    def test_6_check_gift_card_line_amount(self):
        # Amount used by a gift_card can not be more than the cart total/remaining amount
        self.gc1.initial_amount = 10000
        params = {
            "card": self.gc1,
            "gift_card_amount": 10000,
            "code": self.gc1.code,
        }
        gift_card_line = self.cart_service.dispatch(
            "gift_card_amount_validation", params=params
        )

        self.assertEqual(gift_card_line[0].get("amount_used"), self.cart.amount_total)
        self.assertEqual(self.cart.remain_amount, 0)
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)

    def test_7_check_divisible_gift_card_line_amount(self):
        # If the gift card is not divisible,
        # the gift card initial amount will be used,
        # unless it is more than the cart total/remaining amount.
        self.gc1.is_divisible = self.gc2.is_divisible = False

        params = {
            "card": self.gc1,
            "gift_card_amount": 2,
            "code": self.gc1.code,
        }
        gift_card_line_1 = self.cart_service.dispatch(
            "gift_card_amount_validation", params=params
        )

        self.assertEqual(
            gift_card_line_1[0].get("amount_used"), self.gc1.initial_amount
        )
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)

        self.gc2.initial_amount = 50000

        with self.assertRaises(exceptions.UserError) as exc:
            params = {
                "card": self.gc2,
                "gift_card_amount": 10000,
                "code": self.gc2.code,
            }
            self.cart_service.dispatch("gift_card_amount_validation", params=params)

        self.assertEqual(
            exc.exception.name,
            (
                "The Gift Card amount is higher than the current "
                "cart amount, impossible to use the gift card in that case."
            ),
        )
        self.assertEqual(len(self.cart.gift_card_line_ids), 1)

    def test_8_payment_with_gift_card_only(self):
        half_total = self.cart.amount_total / 2

        self.gc1.initial_amount = self.gc2.initial_amount = half_total

        params = {
            "card": self.gc1,
            "gift_card_amount": half_total,
            "code": self.gc1.code,
        }
        self.cart_service.dispatch("gift_card_amount_validation", params=params)

        params = {
            "card": self.gc2,
            "gift_card_amount": half_total,
            "code": self.gc2.code,
        }
        self.cart_service.dispatch("gift_card_amount_validation", params=params)

        params = {
            "cart": self.cart.id,
        }
        self.service_gift_card.dispatch("payment_with_gift_card_only", params=params)

        self.assertEqual("sale", self.cart.state)
        self.assertEqual(len(self.cart.gift_card_line_ids), 2)
        self.assertEqual(2, len(self.cart.transaction_ids))
        self.assertEqual(2, len(self.cart.transaction_ids.payment_id))
