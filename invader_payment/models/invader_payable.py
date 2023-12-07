# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class InvaderPayable(models.AbstractModel):
    """
    Abstract model used to represent a payable recordset.
    When you inherit it, you have to implement these functions if necessary:

    class MyExample(models.Model):
        _name = "my.example"
        _inherit = [_name, "invader.payable"]

        def _invader_prepare_payment_transaction_data(self, acquirer_id):
            vals = super()._invader_prepare_payment_transaction_data(acquirer_id)
            vals.update({
                # ...
            })
            return vals

        def _invader_get_transactions(self):
            # ...

        def _get_shopper_partner(self):
            # ...

        def _get_billing_partner(self):
            # ...

        def _get_delivery_partner(self):
            # ...

        def _get_payable_lines(self):
            # ...
    """

    _name = "invader.payable"
    _description = "Interface for payable objects (e.g. cart, ...)"

    def _invader_prepare_payment_transaction_data(self, acquirer_id):
        """
        Prepare a dictionary to create a ``payment.transaction`` for the
        correct amount and linked to the payable object.

        :param acquirer_id: ``payment.acquirer`` record
        :return: dictionary suitable for ``payment.transaction`` ``create()``
        """
        existing_transactions = len(self._invader_get_transactions()) + 1
        values = {
            "acquirer_id": acquirer_id.id,
            "reference": "{ref}-{nb}".format(
                ref=self._get_internal_ref(), nb=existing_transactions
            ),
            "partner_id": self._get_billing_partner().id,
            # "date": fields.Datetime.now(),
            "amount": self._get_transaction_amount(),
            "currency_id": self._get_transaction_currency().id,
        }
        return_url = acquirer_id._get_filled_url_suffix()
        if return_url:
            values.update({"return_url": return_url})
        return values

    def _invader_get_transactions(self):
        """
        Return payment transaction recordset depending on the payable model
        """
        return self.env["payment.transaction"].browse()

    def _invader_get_transactions_done(self):
        """
        Return only transactions considered as "done".
        - state = "done"
        - state = "authorized" (depending on the provider)
        """
        acquirer_authorize = (
            self.env["payment.acquirer"]
            ._get_feature_support()
            .get("authorize", [])
        )
        transactions = self._invader_get_transactions()
        transactions_done = transactions.filtered(
            lambda tr: tr.state == "done"
        )
        if acquirer_authorize:
            transactions_done |= transactions.filtered(
                lambda tr: tr.acquirer_id.provider in acquirer_authorize
                and tr.state == "authorized"
            )
        return transactions_done

    def _get_payable_lines(self):
        """
        Return payable lines
        """

    def _get_shopper_partner(self):
        return self.env["res.partner"].browse()

    def _get_billing_partner(self):
        return self._get_shopper_partner()

    def _get_delivery_partner(self):
        return self._get_shopper_partner()

    def _get_transaction_amount(self):
        raise NotImplementedError("Amount not implemented for %s" % self._name)

    def _get_transaction_currency(self):
        if hasattr(self, "currency_id"):
            return self.currency_id
        elif hasattr(self, "company_id"):
            return self.company_id.currency_id
        return self.env["res.currency"].browse()

    def _get_internal_ref(self):
        """
        Get the reference to put on the transaction
        """
        raise NotImplementedError()

    def _get_formatted_amount(self, transaction, amount):
        return transaction._get_formatted_amount(force_amount=amount)

    def _prepare_payment_line(self, transaction, line):
        values = {
            "id": line.id,
            "description": line.display_name,
        }
        return values
