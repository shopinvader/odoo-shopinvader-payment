# Copyright 2020 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json
from datetime import datetime, timedelta

import mock
import requests
from odoo.addons.shopinvader.tests.test_cart import CommonConnectedCartCase


class ShopinvaderPaypalPaymentCase(CommonConnectedCartCase):
    def setUp(self, *args, **kwargs):
        super(ShopinvaderPaypalPaymentCase, self).setUp(*args, **kwargs)
        self.acquirer = self.env.ref("payment.payment_acquirer_paypal")
        self.acquirer.paypal_email_account = "test@test.com"
        self.acquirer.state = "test"

    @classmethod
    def setUpClass(cls):
        super(ShopinvaderPaypalPaymentCase, cls).setUpClass()
        cls.cart = cls.env.ref("shopinvader.sale_order_2")
        cls.shopinvader_session = {"cart_id": cls.cart.id}
        with cls.work_on_services(
            cls, partner=None, shopinvader_session=cls.shopinvader_session
        ) as work:
            cls.cart_service = work.component(usage="cart")
            cls.payment_service = work.component(usage="payment_paypal")

    def _get_token_response(self):
        response = requests.Response()
        body = json.dumps(
            dict(
                {
                    "id": "paypal_transaction_test",
                    "links": ["localhost"],
                    "access_token": "the_token",
                    "token_type": "token_type",
                }
            )
        )
        response._content = bytes(body, encoding="utf-8")
        response.encoding = "utf-8"
        response.status_code = 200
        return response

    def _get_paypal_normal_return(self):
        yield self._get_token_response()
        response = requests.Response()
        body = json.dumps(
            dict({"token": "paypal_transaction_test", "status": "COMPLETED"})
        )
        response._content = bytes(body, encoding="utf-8")
        response.encoding = "utf-8"
        response.status_code = 201
        yield response

    def _get_paypal_order(self):
        yield self._get_token_response()
        response = requests.Response()
        body = json.dumps(
            dict(
                {
                    "id": "paypal_transaction_test",
                    "links": [
                        {"rel": "approve", "href": "localhost/redirect"}
                    ],
                    "access_token": "the_token",
                    "token_type": "token_type",
                }
            )
        )
        response._content = bytes(body, encoding="utf-8")
        response.encoding = "utf-8"
        response.status_code = 201

        yield response

    def test_payment_paypal_service_succeeded(self):
        self.assertFalse(self.cart.transaction_ids)
        with mock.patch.object(requests, "post") as mock_request:
            # Simulate checkout
            mock_request.side_effect = self._get_paypal_order()
            self.payment_service.dispatch(
                "checkout_order",
                params={
                    "target": "current_cart",
                    "payment_mode_id": self.acquirer.id,
                    "return_url": "localhost",
                    "cancel_url": "localhost",
                },
            )
            mock_request.side_effect = self._get_paypal_normal_return()
            res = self.payment_service.dispatch(
                "normal_return",
                params={
                    "target": "current_cart",
                    "token": "paypal_transaction_test",
                    "cancel_redirect": "localhost/cancel",
                    "success_redirect": "localhost/success",
                },
            )

        self.assertEquals(1, len(self.cart.transaction_ids))
        self.assertEquals(res["redirect_to"], "localhost/success")
        self.assertEquals("done", self.cart.transaction_ids.state)
        self.assertEquals(
            "paypal_transaction_test",
            self.cart.transaction_ids.acquirer_reference,
        )
        # Simulating automatic confirmation cron (The transaction has to
        # be done for 10 minutes at least)
        self.cart.transaction_ids.write(
            {"date": datetime.now() - timedelta(minutes=10)}
        )
        # As Odoo is in cron context, they do commit.
        # mock commit to avoid test rollback error
        with mock.patch.object(self.env.cr, "commit"):
            self.env["payment.transaction"]._cron_post_process_after_done()
            self.assertEquals("sale", self.cart.state)
