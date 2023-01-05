# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tools.float_utils import float_round

from odoo.addons.component.core import AbstractComponent


class AbstractPayableSaleService(AbstractComponent):
    _inherit = "base.shopinvader.service"
    _name = "shopinvader.abstract.payable.sale.service"

    def _get_available_payment_methods(self, sale):
        return sale.shopinvader_backend_id.payment_method_ids

    def _get_existing_transactions(self, sale):
        return sale.transaction_ids

    def _get_shopinvader_payment_data(self, sale):
        """
        Specific method to shopinvader to retrieve the payment dict information
        to pass to the front-end
        * Available methods
        * The acquirer
        * The amount
        # TODO: For retro compatibility with services return content, we
                let the dict keys unchanged. To be changed in next version
        :return:
        """
        payment_methods = self._get_available_payment_methods(sale)
        currency = sale.currency_id
        transactions = self._get_existing_transactions(sale)
        amount_paid = float_round(sum(transactions.filtered(lambda l: l.state in ["authorized", "done"]).mapped("amount")), precision_rounding=currency.rounding)
        values = {
            "available_methods": {
                "count": len(payment_methods),
                "items": self._get_payment_method_data(payment_methods),
            },
            "existing_transactions": {
                "count": len(transactions),
                "items": self._get_transaction_data(transactions),
            },
            "amount": sale.amount_total - amount_paid,
            "amount_paid": amount_paid,
            "amount_total": sale.amount_total,
        }
        return values

    def _get_transaction_data(self, transactions):
        res = []
        for transaction in transactions:
            res.append(
                {
                    "id": transaction.id,
                    "name": transaction.reference,
                    "payment_method_id": transaction.acquirer_id.id,
                    "payment_method_name": transaction.acquirer_id.name,
                    "date": transaction.date,
                    "amount": transaction.amount,
                    "state": transaction.state,
                }
            )
        return res

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
