# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .fake_payment import (
    FakePaymentElectronic,
    FakePaymentManual,
    PaymentServiceElectronicShopinvader,
    PaymentServiceManualShopinvader,
)


class CommonPaymentCase:
    @classmethod
    def _build_payment_components(cls):
        FakePaymentManual._build_component(cls._components_registry)
        PaymentServiceManualShopinvader._build_component(cls._components_registry)
        FakePaymentElectronic._build_component(cls._components_registry)
        PaymentServiceElectronicShopinvader._build_component(cls._components_registry)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_payment_components()
        cls._create_acquirers()

    @classmethod
    def _create_acquirers(cls):
        cls.acquirer_obj = cls.env["payment.acquirer"]
        payment_journal = cls.env["account.journal"].create(
            {
                "name": "Shopinvader Payments - Test",
                "type": "cash",
                "code": "SHOP - Test",
            }
        )
        vals = {
            "name": "Manual Fake",
            "provider": "manual",
            "journal_id": payment_journal.id,
        }
        cls.acquirer_manual = cls.acquirer_obj.create(vals)
        vals = {
            "name": "Electronic Fake",
            "provider": "manual",  # need to use this to depend only on payment
            "journal_id": payment_journal.id,
        }
        cls.acquirer_electronic = cls.acquirer_obj.create(vals)
        cls.backend.write(
            {
                "payment_method_ids": [
                    (
                        0,
                        0,
                        {
                            "acquirer_id": cls.acquirer_manual.id,
                            "code": "fake_manual",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "acquirer_id": cls.acquirer_electronic.id,
                            "code": "fake_electronic",
                        },
                    ),
                ]
            }
        )
