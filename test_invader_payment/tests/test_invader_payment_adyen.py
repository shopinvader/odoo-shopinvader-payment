# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (https://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import TestCommonPayment


class TestInvaderPaymentAdyen(TestCommonPayment):
    def setUp(self):
        super(TestInvaderPaymentAdyen, self).setUp()
        self.transaction_obj = self.env["payment.transaction"]
        self.payment_mode = self.env.ref(
            "invader_payment_adyen.payment_mode_adyen"
        )
        self.service = self._get_service("payment_adyen")
        key = (
            "DFB1EB5485895CFA84146406857104AB"
            "B4CBCABDC8AAF103A624C8F6A3EAAB00"
        )
        self.payment_mode.payment_acquirer_id.adyen_skin_hmac_key = key

        # Creating a transaction
        vals = {
            "acquirer_id": self.payment_mode.payment_acquirer_id.id,
            "amount": 1000.0,
            "reference": "PARTNER 1",
            "currency_id": self.env.ref("base.EUR").id,
        }
        self.transaction = self.transaction_obj.create(vals)

    def test_notification(self):
        self.transaction.acquirer_reference = "pspReference"
        request = {
            "live": "false",
            "notificationItems": [
                {
                    "NotificationRequestItem": {
                        "additionalData": {
                            "hmacSignature": "18AAP/S+vexKqyNtXIbrqJka0Oq+fuYpt9b8hPRapRM="
                        },
                        "pspReference": "pspReference",
                        "originalReference": "originalReference",
                        "merchantAccount": "merchantAccount",
                        "amount": {"currency": "EUR", "value": 100000},
                        "eventCode": "AUTHORISATION",
                        "success": "true",
                    }
                }
            ],
        }

        self.service.dispatch("webhook", params=request)
        self.assertEquals("done", self.transaction.state)
