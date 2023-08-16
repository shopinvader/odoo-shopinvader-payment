# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class PaymentTransactionPagseguro(models.Model):
    _inherit = "payment.transaction"

    def _get_pagseguro_charge_params(self):
        """
        Returns dict containing the required body information to create a
        charge on Pagseguro.

        Uses the payment amount, currency and encrypted credit card.

        Returns:
            dict: Charge parameters
        """
        CHARGE_PARAMS = {
            "reference_id": str(self.payment_token_id.acquirer_id.id),
            "description": self.display_name[:13],
            "amount": {
                # Charge is in BRL cents -> Multiply by 100
                "value": int(self.amount * 100),
                "currency": "BRL",
            },
            "payment_method": {
                # "soft_descriptor": "", # caso seja usado só aceita 13 caracteres.
                "type": "CREDIT_CARD",
                "installments": 1,
                "capture": False,
                "card": {
                    "encrypted": self.payment_token_id.pagseguro_card_token,
                },
            },
        }

        return CHARGE_PARAMS
