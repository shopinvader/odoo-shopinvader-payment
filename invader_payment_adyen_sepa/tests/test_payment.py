# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import Adyen

from ..models.payment_transaction import ADYEN_SEPA_PAYMENT_METHOD
from .common import TestCommon


class TestPaymentTransaction(TestCommon):
    """
    Tests for payment.transaction
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.adyen = Adyen.Adyen(
            platform=cls.acquirer.state,
            live_endpoint_prefix=cls.acquirer.adyen_live_endpoint_prefix,
            xapikey=cls.acquirer.adyen_api_key,
        )

    def _create_transaction(self, payment_order):
        return payment_order._generate_transaction_adyen()

    def test_payment1(self):
        # Preparation of the Adyen request
        self.invoice.action_post()
        self._wizard_fill_payment_lines(self.payment_order)
        transaction = self._create_transaction(self.payment_order)
        self.assertEqual(transaction.state, "draft")
        self.assertEqual(
            transaction.adyen_payment_method, ADYEN_SEPA_PAYMENT_METHOD
        )

        payment_method = {"type": ADYEN_SEPA_PAYMENT_METHOD}
        payable_request = transaction._prepare_adyen_payments_request(
            payment_method
        )
        with self._call_adyen_payments(payable_request):
            response = self.adyen.checkout.payments(payable_request)
        self.assertEqual(response.status_code, 200)
        transaction._update_with_adyen_response(response)
        self.assertEqual("Authorised", response.message.get("resultCode"))
        self.assertEqual(
            response.message.get("pspReference"),
            transaction.acquirer_reference,
        )
        self.assertEqual(
            ADYEN_SEPA_PAYMENT_METHOD, transaction.adyen_payment_method
        )
