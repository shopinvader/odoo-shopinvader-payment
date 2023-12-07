# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from contextlib import contextmanager
from uuid import uuid4

import Adyen
import mock
from werkzeug import urls

from odoo.addons.component.tests.common import SavepointComponentCase


class TestStockPicking(SavepointComponentCase):
    """
    Tests for stock.picking
    """

    @classmethod
    def setUpClass(cls):
        """
        Memo: The country matters for payment options (klarna not available everywhere)
        """
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.ResPartner = cls.env["res.partner"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.PaymentAcquirer = cls.env["payment.acquirer"]
        cls.euro = cls.env.ref("base.EUR")
        # If no env data are set, we have to force the response of Adyen call.
        cls.force_mock = not bool(os.environ.get("ADYEN_API_KEY", False))
        cls.acquirer = acquirer = cls.PaymentAcquirer.create(
            {
                "name": "Shopinvader Adyen - Unit test",
                "provider": "adyen",
                "adyen_hmac_key": "dummy",
                "adyen_checkout_api_url": "dummy",
                "state": "test",
                "adyen_live_endpoint_prefix": os.environ.get(
                    "ADYEN_API_PREFIX", "empty"
                ),
                "adyen_api_key": os.environ.get("ADYEN_API_KEY", "empty"),
                "adyen_merchant_account": os.environ.get(
                    "ADYEN_MERCHANT_ACCOUNT", "empty"
                ),
                "view_template_id": cls.env["ir.ui.view"]
                .search([("type", "=", "qweb")], limit=1)
                .id,
            }
        )
        cls.belgium = cls.env.ref("base.be")
        # The country matters for payment options (klarna not available everywhere)
        # cls.belgium = cls.env.ref("base.es")
        cls.product = cls.env.ref("product.product_product_4")
        cls.product_2 = cls.env.ref("product.product_product_5")
        cls.adyen = Adyen.Adyen(
            platform=acquirer.state,
            live_endpoint_prefix=acquirer.adyen_live_endpoint_prefix,
            xapikey=acquirer.adyen_api_key,
        )
        cls.partner = cls.ResPartner.create(
            {
                "name": "Sale Partner",
                "street": "Main street",
                "city": "Tintigny",
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
        adyen_service = self._components_registry.get("payment.service.adyen")(
            {}
        )
        return adyen_service

    @contextmanager
    def _mock_adyen_payment_methods(self):
        if self.force_mock:
            fake_response = Adyen.client.AdyenResult()
            fake_response.details = {}
            fake_response.message = {
                "paymentMethods": [
                    {
                        "brands": ["bcmc", "visa"],
                        "name": "Bancontact card",
                        "type": "bcmc",
                    },
                    {"name": "Virement bancaire.", "type": "directEbanking"},
                    {"name": "Payer Maintenant", "type": "klarna_paynow"},
                    {
                        "brands": ["bcmc", "mc", "visa", "amex"],
                        "name": "Carte bancaire",
                        "type": "scheme",
                    },
                    {"name": "Payer Plus Tard", "type": "klarna"},
                    {"name": "Paysafecard", "type": "paysafecard"},
                    {"name": "Prélèvement SEPA", "type": "sepadirectdebit"},
                ],
            }
            fake_response.psp = str(uuid4()).replace("-", "")[:16].upper()
            fake_response.status_code = 200
            with mock.patch.object(
                type(self.adyen.checkout),
                "payment_methods",
                return_value=fake_response,
            ):
                yield
        else:
            yield

    @contextmanager
    def _mock_adyen_payments(self):
        # https://docs.adyen.com/online-payments/build-your-integration/
        # ?platform=Web&integration=API+only&version=70
        fake_response = Adyen.client.AdyenResult()
        fake_response.details = {}
        fake_response.message = {
            "resultCode": "RedirectShopper",
            "action": {
                "paymentMethodType": "klarna",
                "url": "https://checkoutshopper-test.adyen.com/checkoutshopper/"
                "checkoutPaymentRedirect?redirectData=titi",
                "method": "GET",
                "type": "redirect",
            },
        }
        fake_response.psp = str(uuid4()).replace("-", "")[:16].upper()
        fake_response.status_code = 200
        if self.force_mock:
            with mock.patch.object(
                type(self.adyen.checkout),
                "payments",
                return_value=fake_response,
            ):
                yield
        else:
            yield

    @contextmanager
    def _mock_adyen_capture(self):
        # https://docs.adyen.com/online-payments/build-your-integration/
        # ?platform=Web&integration=API+only&version=70
        psp_inside = str(uuid4()).replace("-", "")[:16].upper()
        fake_response = Adyen.client.AdyenResult()
        fake_response.details = {}
        fake_response.message = {
            "pspReference": psp_inside,
            "response": "[capture-received]",
        }
        fake_response.psp = psp_inside
        fake_response.status_code = 200
        if self.force_mock:
            with mock.patch.object(
                type(self.adyen.payment),
                "capture",
                return_value=fake_response,
            ):
                yield
        else:
            yield

    def _prepare_checkout(self):
        request = {
            "merchantAccount": self.acquirer.adyen_merchant_account,
            "channel": "Web",
            "countryCode": self.belgium.code,
            "shopperLocale": "fr-BE",
            "amount": {
                "value": 1000,
                "currency": self.euro.name,
            },
        }
        with self._mock_adyen_payment_methods():
            response = self.adyen.checkout.payment_methods(request)
        message = response.message
        self.assertTrue(
            any(
                "klarna" in pm.get("type", "")
                for pm in message.get("paymentMethods", [])
            )
        )
        self.assertEqual(response.status_code, 200)
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        pay_request = {
            "merchantAccount": self.acquirer.adyen_merchant_account,
            "channel": "Web",
            "countryCode": self.belgium.code,
            "shopperLocale": "fr-BE",
            "amount": {
                "value": 1000,
                "currency": "EUR",
            },
            "reference": str(uuid4()),
            "shopperReference": str(uuid4()),
            "paymentMethod": {
                "type": "klarna",  # BE
                # "type": "klarna_account",  # ES
            },
            "returnUrl": urls.url_join(base_url, "/payment/process"),
            # "additionalData": {
            #     "executeThreeD": True,
            #     # https://docs.adyen.com/development-resources/testing/result-codes/
            #     "RequestedTestAcquirerResponseCode": 1,
            # },
        }
        transaction_values = {
            "amount": self.sale_order.amount_total,
            "currency_id": self.sale_order.currency_id.id,
            "partner_id": self.sale_order.partner_id.id,
            "acquirer_id": self.acquirer.id,
            "sale_order_ids": [(6, 0, self.sale_order.ids)],
        }
        transaction = self.env["payment.transaction"].create(
            transaction_values
        )
        return pay_request, transaction

    def test_checkout1(self):
        """
        Example of return:
        - The redirect to do the payment (easy to have: adyen.checkout.payments(...) )
        {
            'resultCode': 'RedirectShopper',
            'action': {
                'paymentMethodType': 'klarna',
                'url': 'https://checkoutshopper-test.adyen.com/XXX',
                'method': 'GET',
                'type': 'redirect'
            }
        }
        - The return after the payment is validated
        {
            'additionalData': {
                'pspref': 'CG289MWTZSGLNK82',
                'klarnapayments.session_id': 'XXX',
                'recurring.recurringDetailReference': 'XXX',
                'recurring.shopperReference': 'WLU22023000425',
                'recurringContract': 'true',
                'klarnapayments.order_id': 'XXX',
                'issuer': '',
                'shopperReference': 'WLU22023000425'
            },
            'pspReference': 'PSPXXX',
            'resultCode': 'Authorised',
            'amount': {'currency': 'EUR', 'value': 1692},
            'merchantReference': 'WLU22023000425-1',
            'paymentMethod': {'type': 'klarna'}
        }
        """
        # Preparation of the Adyen request
        pay_request, transaction = self._prepare_checkout()
        payment_method = pay_request.get("paymentMethod")
        payable_request = self.sale_order._prepare_adyen_payment_klarna(
            transaction, payment_method
        )
        pay_request.update(payable_request)
        # https://docs.adyen.com/online-payments/build-your-integration/
        # ?platform=Web&integration=API+only&version=70
        with self._mock_adyen_payments():
            response = self.adyen.checkout.payments(pay_request)
        self.assertEqual(response.status_code, 200)
        adyen_service = self._get_adyen_service()
        adyen_service._update_transaction_with_response(transaction, response)
        self.assertIn("action", response.message)
        self.assertEqual("RedirectShopper", response.message.get("resultCode"))
        self.assertEqual(response.psp, transaction.acquirer_reference)
        self.assertEqual("klarna", transaction.adyen_payment_method)

    def test_checkout_and_capture1(self):
        # Preparation of the Adyen request
        pay_request, transaction = self._prepare_checkout()
        self.assertEqual("draft", transaction.state)
        payment_method = {"type": "klarna"}
        payable_request = self.sale_order._prepare_adyen_payment_klarna(
            transaction, payment_method
        )
        pay_request.update(payable_request)
        with self._mock_adyen_payments():
            response = self.adyen.checkout.payments(pay_request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("action", response.message)
        self.assertEqual("RedirectShopper", response.message.get("resultCode"))
        adyen_service = self._get_adyen_service()
        adyen_service._update_transaction_with_response(transaction, response)
        self.assertEqual(response.psp, transaction.acquirer_reference)
        self.assertEqual("klarna", transaction.adyen_payment_method)
        # Now manage the capture
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual("draft", transaction.state)
        transaction._set_transaction_done()
        self.assertEqual("authorized", transaction.state)
        with self._mock_adyen_capture():
            picking.button_validate()
        # The queue job should be disabled to have the transaction is done directly
        self.assertEqual("done", transaction.state)

    def test_invalid_webhook_for_capture(self):
        """
        Example of full webhook
        {
            'live': True,
            'notificationItems':
                [
                    {
                        'NotificationRequestItem': {
                        'additionalData': {
                            'hmacSignature': 'xxx',
                            'bookingDate': '2023-03-14T14:13:09Z'
                        },
                        'amount': {
                            'currency': 'EUR',
                            'value': 4297
                        },
                        'eventCode': 'REFUND',
                        'eventDate': '2023-03-14T14:12:04+01:00',
                        'merchantAccountCode': 'Debreuyn',
                        'merchantReference': 'Gutschrift AR/2023/1004',
                        'originalReference': 'DHMLTHTG79CTF232',
                        'paymentMethod': 'klarna',
                        'pspReference': 'XZK9KF7JGRLZ2C32',
                        'reason': '',
                        'success': 'true'
                    }
                }
            ]
        }
        """
        # Preparation of the Adyen request
        pay_request, transaction = self._prepare_checkout()
        self.assertEqual("draft", transaction.state)
        payment_method = {"type": "klarna"}
        payable_request = self.sale_order._prepare_adyen_payment_klarna(
            transaction, payment_method
        )
        pay_request.update(payable_request)
        with self._mock_adyen_payments():
            response = self.adyen.checkout.payments(pay_request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("action", response.message)
        self.assertEqual("RedirectShopper", response.message.get("resultCode"))
        adyen_service = self._get_adyen_service()
        adyen_service._update_transaction_with_response(transaction, response)
        self.assertEqual(response.psp, transaction.acquirer_reference)
        self.assertEqual("klarna", transaction.adyen_payment_method)
        # Now manage the capture
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids)
        self.assertEqual("draft", transaction.state)
        transaction._set_transaction_done()
        self.assertEqual("authorized", transaction.state)
        # Simulate webhook
        request_item = {
            "NotificationRequestItem": {
                "additionalData": {
                    "expiryDate": "06/2026",
                    "authCode": "ODJZOV",
                    "cardSummary": "0311",
                    "cardHolderName": " /",
                    "shopperInteraction": "Ecommerce",
                    "hmacSignature": transaction.acquirer_id.adyen_hmac_key,
                },
                "amount": pay_request.get("amount", {}),
                "eventCode": "AUTHORISATION",
                "eventDate": "2023-03-14T13:22:32+01:00",
                "merchantAccountCode": transaction.acquirer_id.adyen_merchant_account,
                "merchantReference": transaction.reference,
                "paymentMethod": "klarna",
                "pspReference": transaction.acquirer_reference,
                "reason": "abc",
                "success": "true",
            }
        }
        transaction._handle_adyen_notification_item_authorized(
            request_item.get("NotificationRequestItem")
        )
        # Transaction should stay in the same state because it's not a capture
        self.assertEqual("authorized", transaction.state)

    def test_correct_webhook_for_capture(self):
        """
        Example of full webhook
        {
            'live': True,
            'notificationItems':
                [
                    {
                        'NotificationRequestItem': {
                        'additionalData': {
                            'hmacSignature': 'xxx',
                            'bookingDate': '2023-03-14T14:13:09Z'
                        },
                        'amount': {
                            'currency': 'EUR',
                            'value': 4297
                        },
                        'eventCode': 'REFUND',
                        'eventDate': '2023-03-14T14:12:04+01:00',
                        'merchantAccountCode': 'Debreuyn',
                        'merchantReference': 'Gutschrift AR/2023/1004',
                        'originalReference': 'DHMLTHTG79CTF232',
                        'paymentMethod': 'klarna',
                        'pspReference': 'XZK9KF7JGRLZ2C32',
                        'reason': '',
                        'success': 'true'
                    }
                }
            ]
        }
        """
        # Preparation of the Adyen request
        pay_request, transaction = self._prepare_checkout()
        self.assertEqual("draft", transaction.state)
        payment_method = {"type": "klarna"}
        payable_request = self.sale_order._prepare_adyen_payment_klarna(
            transaction, payment_method
        )
        pay_request.update(payable_request)
        with self._mock_adyen_payments():
            response = self.adyen.checkout.payments(pay_request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("action", response.message)
        self.assertEqual("RedirectShopper", response.message.get("resultCode"))
        adyen_service = self._get_adyen_service()
        adyen_service._update_transaction_with_response(transaction, response)
        self.assertEqual(response.psp, transaction.acquirer_reference)
        self.assertEqual("klarna", transaction.adyen_payment_method)
        # Now manage the capture
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertTrue(picking)
        self.assertEqual("draft", transaction.state)
        transaction._set_transaction_done()
        self.assertEqual("authorized", transaction.state)
        # Simulate webhook
        request_item = {
            "NotificationRequestItem": {
                "additionalData": {
                    "expiryDate": "06/2026",
                    "authCode": "ODJZOV",
                    "cardSummary": "0311",
                    "cardHolderName": " /",
                    "shopperInteraction": "Ecommerce",
                    "hmacSignature": transaction.acquirer_id.adyen_hmac_key,
                },
                "amount": pay_request.get("amount", {}),
                "eventCode": "CAPTURE",
                "eventDate": "2023-03-14T13:22:32+01:00",
                "merchantAccountCode": transaction.acquirer_id.adyen_merchant_account,
                "merchantReference": transaction.reference,
                "paymentMethod": "klarna",
                "pspReference": transaction.acquirer_reference,
                "reason": "abc",
                "success": "true",
            }
        }
        transaction._handle_adyen_notification_item_capture(
            request_item.get("NotificationRequestItem")
        )
        self.assertEqual("done", transaction.state)
