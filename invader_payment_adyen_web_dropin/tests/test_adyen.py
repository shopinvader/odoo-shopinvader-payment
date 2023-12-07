# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from contextlib import contextmanager
from datetime import timedelta
from uuid import uuid4

import Adyen
import mock
from Adyen.util import generate_notification_sig

from odoo import api, fields
from odoo.tools import mute_logger

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.website.tools import MockRequest

from ..models.payment_acquirer import ADYEN_PROVIDER


class TestAdyenPayment(SavepointComponentCase):
    """
    Tests for Adyen payments with simple flow
    https://docs.adyen.com/online-payments/build-your-integration/
    ?platform=Web&integration=Drop-in&version=5.55.1
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                test_queue_job_no_delay=True,
            )
        )
        cls.ResPartner = cls.env["res.partner"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.PaymentAcquirer = cls.env["payment.acquirer"]
        cls.euro = cls.env.ref("base.EUR")
        cls.acquirer = acquirer = cls.env["payment.acquirer"].search(
            [("provider", "=", ADYEN_PROVIDER)], limit=1
        )
        cls.fake_url = "titi.be"
        cls.force_mock = not bool(os.environ.get("ADYEN_API_KEY", False))
        cls.acquirer.write(
            {
                "state": "test",
                "adyen_dropin_live_endpoint_prefix": os.environ.get(
                    "ADYEN_API_PREFIX", "empty"
                ),
                "adyen_dropin_api_key": os.environ.get(
                    "ADYEN_API_KEY", str(uuid4()).replace("-", "")
                ),
                "adyen_dropin_merchant_account": os.environ.get(
                    "ADYEN_MERCHANT_ACCOUNT", "empty"
                ),
                "adyen_dropin_webhook_hmac": os.environ.get(
                    "ADYEN_HMAC", str(uuid4()).replace("-", "")
                ),
            }
        )
        # The country matters for payment options availability
        cls.belgium = cls.env.ref("base.be")
        cls.product = cls.env.ref("product.product_product_4")
        cls.product_2 = cls.env.ref("product.product_product_5")
        cls.adyen = Adyen.Adyen(
            platform=acquirer.state,
            live_endpoint_prefix=acquirer.adyen_dropin_live_endpoint_prefix,
            xapikey=acquirer.adyen_dropin_api_key,
        )
        cls.partner = cls.ResPartner.create(
            {
                "name": "Sale Partner",
                "street": "Main street",
                "city": "Tintigny-les-bains",
                "country_id": cls.belgium.id,
                "zip": "6730",
            }
        )
        cls.sale_order = cls.SaleOrder.create(
            {
                "name": "TestSO",
                "partner_id": cls.partner.id,
                "partner_invoice_id": cls.partner.id,
                "partner_shipping_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 2,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": cls.product.list_price,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.product_2.name,
                            "product_id": cls.product_2.id,
                            "product_uom_qty": 2,
                            "product_uom": cls.product_2.uom_id.id,
                            "price_unit": cls.product_2.list_price,
                        },
                    ),
                ],
            }
        )

    def _get_adyen_service(self):
        adyen_service = self._components_registry.get(
            "payment.service.adyen_web_dropin"
        )(
            WorkContext(
                collection=_PseudoCollection(env=self.env, name="sale.order"),
                model_name="sale.order",
            )
        )
        return adyen_service

    @contextmanager
    def _mock_adyen_session(self, payable):
        if self.force_mock:
            now_tz = fields.Datetime.context_timestamp(
                self.env.user, fields.Datetime.now()
            )
            # Default session's expiration is 1 hour
            expiration = now_tz + timedelta(hours=1)
            fake_response = Adyen.client.AdyenResult()
            fake_response.details = {}
            fake_response.message = {
                "amount": {
                    "currency": payable._get_transaction_currency().name,
                    "value": payable._get_transaction_amount() * 100,
                },
                "applicationInfo": {
                    "adyenLibrary": {
                        "name": "adyen-python-api-library",
                        "version": "7.0.0",
                    }
                },
                "countryCode": payable._get_billing_partner().country_id.code,
                "expiresAt": expiration.isoformat(),
                "id": str(uuid4()).replace("-", "")[:18].upper(),
                "merchantAccount": self.acquirer.adyen_dropin_merchant_account,
                "reference": payable._get_internal_ref(),
                "returnUrl": "false",
                "shopperLocale": payable.env.lang or "en_US",
                "sessionData": str(uuid4()),
            }
            fake_response.psp = str(uuid4()).replace("-", "")[:16].upper()
            fake_response.status_code = 201
            with mock.patch.object(
                type(self.adyen.checkout),
                "sessions",
                return_value=fake_response,
            ):
                yield
        else:
            yield

    @contextmanager
    def _mock_adyen_session_response(self, transaction, adyen_response):
        now = fields.Datetime.context_timestamp(
            transaction, fields.Datetime.now()
        )
        fake_response = {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "eventCode": "AUTHORISATION",
                        "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
                        "reason": "033899:1111:03/2030",
                        "amount": transaction._get_formatted_amount(),
                        "operations": ["CANCEL", "CAPTURE", "REFUND"],
                        "success": "true",  # This define if the payment is ok
                        "paymentMethod": "mc",
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": adyen_response.message.get(
                                "id"
                            ),
                            "hmacSignature": "xxx",  # TODO
                        },
                        "merchantReference": adyen_response.message.get(
                            "reference"
                        ),
                        "pspReference": str(uuid4())
                        .replace("-", "")[:16]
                        .upper(),
                        "eventDate": now.isoformat(),
                    }
                }
            ],
        }

        @api.model
        def manage_adyen_dropin_webhook(this_self, response, queue_job=False):
            return this_self.manage_adyen_dropin_webhook.origin(
                fake_response, queue_job=queue_job
            )

        Transaction = self.env["payment.transaction"]
        Transaction._patch_method(
            "manage_adyen_dropin_webhook", manage_adyen_dropin_webhook
        )
        yield
        Transaction._revert_method("manage_adyen_dropin_webhook")

    def test_payments_response1(self):
        """
        Example of return:

        """
        # Get json on a payable object
        # Give it to Adyen
        # Check result
        payable = self.sale_order
        adyen_service = self._get_adyen_service()
        # Mock it to avoid NotImplementedError Exception.
        with mock.patch.object(
            type(adyen_service.payment_service),
            "_invader_find_payable_from_target",
            return_value=payable,
        ):
            self.assertFalse(payable.transaction_ids)
            with MockRequest(self.env) as req:
                req.httprequest.url = self.fake_url
                req.httprequest.environ = {"REMOTE_ADDR": "127.0.0.1"}
                with self._mock_adyen_session(payable):
                    response = adyen_service.payments(
                        payable, acquirer_id=self.acquirer.id
                    )
                # Todo: check the dict used to create the session
                session_data = payable.transaction_ids._prepare_adyen_session()
            transaction = payable.transaction_ids
            # {
            #     'merchantAccount': 'xxx',
            #     'amount': {'value': 179400, 'currency': 'USD'},
            #     'returnUrl': False,
            #     'reference': 'TestSO',
            #     'countryCode': 'BE',
            #     'shopperLocale': 'en_US',
            # }
            self.assertEqual(len(transaction), 1)
            self.assertTrue(transaction.acquirer_reference)
            self.assertEqual(
                transaction.acquirer_reference, response.get("id")
            )
            self.assertEqual(transaction.acquirer_id, self.acquirer)
            self.assertEqual(
                session_data.get("merchantAccount"),
                transaction.acquirer_id.adyen_dropin_merchant_account,
            )
            self.assertEqual(
                session_data.get("amount", {}).get("currency"),
                payable.currency_id.name,
            )
            self.assertEqual(
                session_data.get("amount", {}).get("value"),
                transaction._get_formatted_amount(),
            )
            self.assertEqual(session_data.get("returnUrl", False), False)
            self.assertEqual(
                session_data.get("reference"),
                payable._get_internal_ref() + "-1",
            )
            self.assertEqual(
                session_data.get("countryCode"),
                payable.partner_id.country_id.code,
            )
            self.assertEqual(
                session_data.get("shopperLocale"), payable.env.lang or "en_US"
            )
            # Now check the result
            self.assertIsInstance(response, dict)
            # Example of response.message
            # {
            #     'amount': {'currency': 'USD', 'value': 179400},
            #     'applicationInfo': {
            #         'adyenLibrary': {'name': 'adyen-python-api-library', 'version': '7.0.0'}
            #     },
            #     'countryCode': 'BE',
            #     'expiresAt': '2024-01-05T15:28:18+01:00',
            #     'id': 'CSB34693538155517E',
            #     'merchantAccount': 'xxx',
            #     'reference': 'TestSO',
            #     'returnUrl': 'false',
            #     'shopperLocale': 'en_US',
            #     'sessionData': 'xxx',
            # }
            self.assertEqual(
                response.get("amount", {}).get("currency"),
                payable.currency_id.name,
            )
            self.assertEqual(
                response.get("amount", {}).get("value"),
                payable.amount_total * 100,
            )
            self.assertEqual(
                response.get("countryCode"),
                payable.partner_id.country_id.code,
            )
            self.assertTrue(response.get("id"))
            self.assertTrue(response.get("expiresAt"))
            self.assertEqual(
                response.get("merchantAccount"),
                self.acquirer.adyen_dropin_merchant_account,
            )
            self.assertEqual(
                response.get("reference"), payable._get_internal_ref() + "-1"
            )
            self.assertEqual(response.get("returnUrl"), "false")
            self.assertEqual(
                response.get("shopperLocale"),
                payable.env.lang or "en_US",
            )

    def test_payments_result_accepted1(self):
        """
        https://docs.adyen.com/online-payments/build-your-integration/
        ?platform=Web&integration=Drop-in&version=5.55.1&tab=python_6
        #update-your-order-management-system
        Each webhook need to return a string with [accepted]
        https://docs.adyen.com/development-resources/webhooks/#accept-webhooks
        Example of return by Adyen:
        {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "eventCode": "AUTHORISATION",
                        "merchantAccountCode": "YOUR_MERCHANT_ACCOUNT",
                        "reason": "033899:1111:03/2030",
                        "amount": {
                            "currency":"EUR",
                            "value":2500
                        },
                        "operations": ["CANCEL", "CAPTURE", "REFUND"],
                        "success": "true",  # This define if the payment is ok
                        "paymentMethod": "mc",
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": "CSF46729982237A879",
                            "hmacSignature": "xxx",  # Optionnal
                        },
                        "merchantReference": "YOUR_REFERENCE",
                        "pspReference": "NC6HT9CRT65ZGN82",
                        "eventDate": "2021-09-13T14:10:22+02:00",
                    }
                }
            ]
        }
        """
        payable = self.sale_order
        adyen_service = self._get_adyen_service()
        # Mock it to avoid NotImplementedError Exception.
        with mock.patch.object(
            type(adyen_service.payment_service),
            "_invader_find_payable_from_target",
            return_value=payable,
        ):
            with MockRequest(self.env) as req:
                req.httprequest.url = self.fake_url
                with self._mock_adyen_session(payable):
                    response = adyen_service.payments(
                        payable, acquirer_id=self.acquirer.id
                    )
        transaction = payable.transaction_ids
        self.assertTrue(transaction)
        now = fields.Datetime.context_timestamp(
            transaction, fields.Datetime.now()
        )
        mc = "mc"
        hmac_key = self.acquirer.adyen_dropin_webhook_hmac
        req_item = {
            "eventCode": "AUTHORISATION",
            "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
            "reason": "033899:1111:03/2030",
            "amount": {
                "currency": transaction.currency_id.name,
                "value": transaction._get_formatted_amount(),
            },
            "operations": ["CANCEL", "CAPTURE", "REFUND"],
            "success": "true",  # This define if the payment is ok
            "paymentMethod": mc,
            "merchantReference": response.get("reference"),
            "pspReference": str(uuid4()).replace("-", "")[:16].upper(),
            "eventDate": now.isoformat(),
        }
        # Generate a valid signature with hmac
        merchant_sign = generate_notification_sig(req_item.copy(), hmac_key)
        hmac_signature = merchant_sign.decode("utf-8")
        # The additionalData should be added after the signature generation
        req_item.update(
            {
                "additionalData": {
                    "expiryDate": "03/2030",
                    "authCode": "033899",
                    "cardBin": "411111",
                    "cardSummary": "1111",
                    "checkoutSessionId": response.get("id"),
                    "hmacSignature": hmac_signature,
                },
            }
        )
        fake_response = {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": req_item,
                }
            ],
        }
        with mute_logger("odoo.addons.queue_job.delay"):
            response = adyen_service.webhook(**fake_response.copy())
        self.assertEqual(response, "[accepted]")
        self.assertEqual(transaction.state, "done")
        self.assertEqual(transaction.adyen_payment_method, mc)

    def test_payments_result_accepted2(self):
        """
        https://docs.adyen.com/online-payments/build-your-integration/
        ?platform=Web&integration=Drop-in&version=5.55.1&tab=python_6
        #update-your-order-management-system
        Each webhook need to return a string with [accepted]
        https://docs.adyen.com/development-resources/webhooks/#accept-webhooks
        Example of return by Adyen:
        {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "eventCode": "AUTHORISATION",
                        "merchantAccountCode": "YOUR_MERCHANT_ACCOUNT",
                        "reason": "033899:1111:03/2030",
                        "amount": {
                            "currency":"EUR",
                            "value":2500
                        },
                        "operations": ["CANCEL", "CAPTURE", "REFUND"],
                        "success": "true",  # This define if the payment is ok
                        "paymentMethod": "mc",
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": "CSF46729982237A879",
                            "hmacSignature": "xxx",  # Optionnal
                        },
                        "merchantReference": "YOUR_REFERENCE",
                        "pspReference": "NC6HT9CRT65ZGN82",
                        "eventDate": "2021-09-13T14:10:22+02:00",
                    }
                }
            ]
        }
        For this case, we specify the transaction_id to simulate a direct call
        """
        payable = self.sale_order
        adyen_service = self._get_adyen_service()
        # Mock it to avoid NotImplementedError Exception.
        with mock.patch.object(
            type(adyen_service.payment_service),
            "_invader_find_payable_from_target",
            return_value=payable,
        ):
            with MockRequest(self.env) as req:
                req.httprequest.url = self.fake_url
                with self._mock_adyen_session(payable):
                    response = adyen_service.payments(
                        payable, acquirer_id=self.acquirer.id
                    )
        transaction = payable.transaction_ids
        self.assertTrue(transaction)
        now = fields.Datetime.context_timestamp(
            transaction, fields.Datetime.now()
        )
        mc = "mc"
        hmac_key = self.acquirer.adyen_dropin_webhook_hmac
        req_item = {
            "eventCode": "AUTHORISATION",
            "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
            "reason": "033899:1111:03/2030",
            "amount": {
                "currency": transaction.currency_id.name,
                "value": transaction._get_formatted_amount(),
            },
            "operations": ["CANCEL", "CAPTURE", "REFUND"],
            "success": "true",  # This define if the payment is ok
            "paymentMethod": mc,
            "merchantReference": response.get("reference"),
            "pspReference": str(uuid4()).replace("-", "")[:16].upper(),
            "eventDate": now.isoformat(),
        }
        # Generate a valid signature with hmac
        merchant_sign = generate_notification_sig(req_item.copy(), hmac_key)
        hmac_signature = merchant_sign.decode("utf-8")
        # The additionalData should be added after the signature generation
        req_item.update(
            {
                "additionalData": {
                    "expiryDate": "03/2030",
                    "authCode": "033899",
                    "cardBin": "411111",
                    "cardSummary": "1111",
                    "checkoutSessionId": response.get("id"),
                    "hmacSignature": hmac_signature,
                },
            }
        )
        fake_response = {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": req_item,
                }
            ],
        }
        with mute_logger("odoo.addons.queue_job.delay"):
            response = adyen_service.webhook(
                transaction_id=transaction.id, **fake_response.copy()
            )
        self.assertEqual(response, "[accepted]")
        self.assertEqual(transaction.state, "done")
        self.assertEqual(transaction.adyen_payment_method, mc)

    def test_payments_result_refused1(self):
        """
        https://docs.adyen.com/online-payments/build-your-integration/
        ?platform=Web&integration=Drop-in&version=5.55.1&tab=python_6
        #update-your-order-management-system
        Each webhook need to return a string with [accepted]
        https://docs.adyen.com/development-resources/webhooks/#accept-webhooks
        Example of return by Adyen in case of error:
        {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "eventCode": "AUTHORISATION",
                        "merchantAccountCode": "YOUR_MERCHANT_ACCOUNT",
                        "reason": "You don't have enough money dude!",
                        "amount": {
                            "currency":"EUR",
                            "value":2500
                        },
                        "operations": ["CANCEL", "CAPTURE", "REFUND"],
                        "success": "false",  # This define if the payment is ok
                        "paymentMethod": "abc",
                        "additionalData": {
                            "expiryDate": "03/2030",
                            "authCode": "033899",
                            "cardBin": "411111",
                            "cardSummary": "1111",
                            "checkoutSessionId": "CSF46729982237A879",
                            "hmacSignature": "xxx",  # Optionnal
                        },
                        "merchantReference": "YOUR_REFERENCE",
                        "pspReference": "NC6HT9CRT65ZGN82",
                        "eventDate": "2021-09-13T14:10:22+02:00",
                    }
                }
            ]
        }
        """
        payable = self.sale_order
        adyen_service = self._get_adyen_service()
        # Mock it to avoid NotImplementedError Exception.
        with mock.patch.object(
            type(adyen_service.payment_service),
            "_invader_find_payable_from_target",
            return_value=payable,
        ):
            with MockRequest(self.env) as req:
                req.httprequest.url = self.fake_url
                with self._mock_adyen_session(payable):
                    response = adyen_service.payments(
                        payable, acquirer_id=self.acquirer.id
                    )
        transaction = payable.transaction_ids
        self.assertTrue(transaction)
        now = fields.Datetime.context_timestamp(
            transaction, fields.Datetime.now()
        )
        mc = "unknowncard"
        hmac_key = self.acquirer.adyen_dropin_webhook_hmac
        req_item = {
            "eventCode": "AUTHORISATION",
            "merchantAccountCode": transaction._get_adyen_dropin_merchant_account(),
            "reason": "validation 101 Invalid card number",
            "amount": {
                "currency": transaction.currency_id.name,
                "value": transaction._get_formatted_amount(),
            },
            "operations": ["CANCEL", "CAPTURE", "REFUND"],
            "success": "false",  # This define if the payment is NOT ok
            "paymentMethod": mc,
            "merchantReference": response.get("reference"),
            "pspReference": str(uuid4()).replace("-", "")[:16].upper(),
            "eventDate": now.isoformat(),
        }
        # Generate a valid signature with hmac
        merchant_sign = generate_notification_sig(req_item.copy(), hmac_key)
        hmac_signature = merchant_sign.decode("utf-8")
        # The additionalData should be added after the signature generation
        req_item.update(
            {
                "additionalData": {
                    "expiryDate": "03/2030",
                    "authCode": "033899",
                    "cardBin": "411111",
                    "cardSummary": "1111",
                    "checkoutSessionId": response.get("id"),
                    "hmacSignature": hmac_signature,
                },
            }
        )
        fake_response = {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": req_item,
                }
            ],
        }
        with mute_logger("odoo.addons.queue_job.delay"):
            response = adyen_service.webhook(**fake_response.copy())
        # "accepted" because the transaction is correctly updated
        self.assertEqual(response, "[accepted]")
        self.assertEqual(transaction.state, "error")
        self.assertEqual(transaction.adyen_payment_method, mc)
