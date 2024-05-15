# Copyright 2024 ACSONE SA (https://acsone.eu).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import random
import string

from odoo_test_helper import FakeModelLoader

from odoo.tests.common import tagged

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase

from ..routers.payment import payment_router


@tagged("post_install", "-at_install")
class TestPaymentCommon(FastAPITransactionCase, FakeModelLoader):
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

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import PayableTestModel  # pylint: disable=import-outside-toplevel

        cls.loader.update_registry((PayableTestModel,))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def _create_payable_record(cls, partner):
        return cls.env["payable.test.model"].create(
            {
                "name": "".join(random.choices(string.ascii_lowercase, k=15)),
                "amount": random.randint(1, 200),
                "partner_id": partner.id,
            }
        )
