# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import random
import string

from odoo_test_helper import FakeModelLoader

from odoo.tests.common import tagged

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase

from ..routers.payment import payment_router


@tagged("post_install", "-at_install")
class TestPaymentCommon(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        partner = cls.env["res.partner"].create(
            {"name": "FastAPI Payment Test Partner"}
        )

        cls.user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "user",
                "groups_id": [(6, 0, [])],
            }
        )

        cls.default_fastapi_running_user = cls.user
        cls.default_fastapi_authenticated_partner = partner.with_user(cls.user)
        cls.default_fastapi_router = payment_router

    @classmethod
    def init_provider(cls):
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

        cls.demo_provider = cls.env.ref("payment.payment_provider_demo")
        cls.demo_provider.write({"state": "test", "is_published": True})

        cls.demo_method_1 = cls.env.ref("payment.payment_method_paypal")

        cls.demo_method_2 = cls.env.ref("payment.payment_method_card")

        cls.demo_provider.payment_method_ids = [
            cls.demo_method_1.id,
            cls.demo_method_2.id,
        ]
        cls.demo_method_1.write({"active": True})
        cls.demo_method_2.write({"active": True})

    def setUp(self) -> None:
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()
        from .models import PayableTestModel  # pylint: disable=import-outside-toplevel

        self.loader.update_registry((PayableTestModel,))

    def tearDown(self):
        self.loader.restore_registry()
        super().tearDown()

    def _create_payable_record(self, partner):
        return self.env["payable.test.model"].create(
            {
                "name": "".join(random.choices(string.ascii_lowercase, k=15)),
                "amount": random.randint(1, 200),
                "partner_id": partner.id,
            }
        )
