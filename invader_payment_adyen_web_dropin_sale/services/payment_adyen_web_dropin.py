# Copyright 2024 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import AbstractComponent


class PaymentServiceAdyenWebDropin(AbstractComponent):
    _inherit = "payment.service.adyen_web_dropin"

    def _validator_return_transaction_details(self):
        """
        Returns nothing
        :return:
        """
        validator = super()._validator_return_transaction_details()
        schema = {
            "sale_ids": {
                "type": "list",
                "nullable": False,
                "required": False,
                "schema": {"type": "integer"},
            },
        }
        validator.schema.update(schema)
        return validator

    def transaction_details(self, transaction_id):
        details = super().transaction_details(transaction_id)
        if self.sale_order_ids:
            details.update(
                {
                    "sale_ids": self.sale_order_ids.ids,
                }
            )
        return details
