# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class InvaderPaymentService(Component):

    _name = "invader.payment.service"
    _usage = "invader.payment"

    def _invader_find_payable_from_target(self, target, **params):
        """
        Find an invader.payable from a target parameter (e.g. current cart).

        target and params comply with the schema returned by
        ``_invader_get_target_validator``.
        """
        raise NotImplementedError()

    def _invader_get_target_validator(self):
        """
        Return a cerberus validator schema fragment that specifies the
        target being paid. Implementations must extend it by populating
        the "allowed" field (eg with strings such as 'current_cart') and
        possibly adding other fields.
        """
        return {"target": {"type": "string", "required": True, "allowed": []}}

    def _check_provider(self, acquirer_id, provider):
        """Check that the payment mode has the correct provider
        If the provider is not the same, raise an error
        """
        acquirer = acquirer_id.sudo()
        if acquirer.provider != provider:
            raise UserError(
                _(
                    "Payment mode acquirer mismatch should be " "'{}' instead of '{}'."
                ).format(provider, acquirer.provider)
            )

    def _get_transaction_validator(self):
        """This is intended to be called by each implentation where transactions
        dict is added to response

        :return: _description_
        :rtype: _type_
        """
        return {
            "date": {"type": "datetime"},
            "acquirer": {"type": "dict", "required": True},
            "state": {
                "type": "string",
                "allowed": [
                    "draft",
                    "pending",
                    "authorized",
                    "done",
                    "cancel",
                    "error",
                ],
            },
            "amount": {"type": "float"},
        }

    def _get_transactions_validator(self):
        """This is intended to be called by each implentation where transactions
        dict is added to response

        :return: _description_
        :rtype: _type_
        """
        return {
            "transactions": {
                "type": "list",
                "schema": self._get_transaction_validator(),
            }
        }

    def _json_parser(self):
        res = [
            "id",
            "date",
            ("acquirer_id:acquirer", ["id", "display_name:name"]),
            "state",
            "amount",
        ]
        return res

    # Provide a way to retrieve transactions through payable object
    def _to_json(self, transactions):
        return {"transactions": transactions.jsonify(self._json_parser())}
