# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError as err:
    _logger.debug(err)


class InvoiceService(Component):

    _inherit = "shopinvader.invoice.service"

    def _get_available_payment_methods(self, invoice):
        """
        Get payment method for the given invoice
        :param invoice: account.move recordset
        :return: shopinvader.payment recordset
        """
        return invoice.shopinvader_backend_id.payment_method_ids

    def _get_shopinvader_payment_data(self, invoice):
        """
        Specific method to shopinvader to retrieve the payment dict information
        to pass to the front-end
        * Available methods
        * The payment mode
        * The amount
        :param invoice: account.move recordset
        :return: dict
        """
        payment_methods = self._get_available_payment_methods(invoice)
        selected_method = payment_methods.filtered(
            lambda m: m.acquirer_id.inbound_payment_method_ids.mapped(
                "payment_mode_ids"
            )
            == invoice.payment_mode_id
        )
        values = {
            "available_methods": {
                "count": len(payment_methods),
                "items": self._get_payment_method_data(payment_methods),
            },
            "selected_method": self._get_payment_method_data(selected_method),
            # Don't use amount_total in case if we have partial payment.
            "amount": invoice.amount_residual_signed,
        }
        return values

    def _get_payment_method_data(self, methods):
        res = []
        for method in methods:
            res.append(
                {
                    "id": method.acquirer_id.id,
                    "name": method.acquirer_id.name,
                    # fmt: off
                    "provider":
                        method.acquirer_id.provider,
                    # fmt: on
                    "code": method.code,
                    "description": method.description,
                }
            )
        return res

    def _validator_return_search(self):
        """
        Inherit the return_search validator to allow unknown
        :return: dict
        """
        schema = super()._validator_return_search()
        return Validator(schema, allow_unknown=True)

    def _to_json_invoice(self, invoice):
        """
        Inherit the invoice json to add payment method details
        :param invoice: account.move recordset
        :return: dict
        """
        values = super()._to_json_invoice(invoice)
        payment = self.work.component(usage="invader.payment")
        values.update(payment._to_json(invoice._invader_get_transactions()))
        values.update({"payment": self._get_shopinvader_payment_data(invoice)})
        return values

    def _get_allowed_invoice_states(self):
        """
        Inherit to add also validated invoices
        :return: list of str
        """
        states = super()._get_allowed_invoice_states()
        states.append("open")
        return states
