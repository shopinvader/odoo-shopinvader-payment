# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools.float_utils import float_round


class PaymentTransaction(models.Model):
    """
    To implements depending on the provider:

    ...
    YOUR_PROVIDER_SELECTION = "xxx"

    class PaymentTransaction(models.Model):
        _inherit = "payment.transaction"

        # Required
        def _get_service(self):
            if self.acquirer_id.provider == YOUR_PROVIDER_SELECTION:
                return self._get_xxx_service()
            return super()._get_service()

        def _prepare_transaction_data(self):
            res = super()._prepare_transaction_data()
            if self.acquirer_id.provider == YOUR_PROVIDER_SELECTION:
                res.update(self._prepare_adyen_session())
            return res

        def _trigger_transaction_provider(self, data):
            if self.acquirer_id.provider == YOUR_PROVIDER_SELECTION:
                return self._trigger_transaction_xxx(data)

        def _update_with_response(self, response):
            # Update the transaction depending on the response

        # Optional
        def _get_formatted_amount(self, force_amount=False):
            # If your amount should be formatted (rounding etc) for your provider

        def _parse_transaction_response(self, response):
            # Parse the response to send back to the front side

    To implements if you're applying the transaction on a new payable record:

    class PaymentTransaction(models.Model):
        _inherit = "payment.transaction"

        def _get_invader_payables(self):
            return your_recordset
    """

    _inherit = "payment.transaction"

    def _get_platform(self):
        """
        :return: str
        """
        return ""

    def _get_invader_payables(self):
        """
        Returns the invader_payable objects this transaction applies to
        Each time the sate of a transaction changes an event is notified to
        the invader_payables for the new state. The event name is formatted as
        '_on_payment_transaction_' + state:

        To be notified when one of these events occurs you must declare an
        event listener as:

        from odoo.addons.component.core import Component

        class MyInvaderPayableListener(Component):
            _name = 'my.invader.payable.event.listener'
            _inherit = 'base.event.listener'
            _apply_on = ['my.invader.payable']

            def on_payment_transaction_draft(
                self, invader_payable, transaction):
                pass
            ...

        """
        self.ensure_one()
        return None

    def _get_service(self):
        raise NotImplementedError()

    @api.model_create_multi
    def create(self, list_vals):
        records = super().create(list_vals)
        records._notify_state_changed_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            self._notify_state_changed_event()
        return res

    def _notify_state_changed_event(self):
        """
        Notify the invader_payable that the state of the transaction
        has changed
        """
        for record in self:
            payables = record._get_invader_payables()
            if not payables:
                continue
            for payable in payables:
                state = record.state
                event_name = "on_payment_transaction_{}".format(state)
                payable._event(event_name).notify(payable, record)

    @api.model
    def _get_formatted_amount(self, force_amount=False):
        """
        Get the amount of the transaction in correct format for the provider
        :param amount: float
        :return: int
        """
        dp_name = self.acquirer_id.provider or ""
        if dp_name:
            dp_name = dp_name.capitalize()
        digits = self.env["decimal.precision"].precision_get(dp_name)
        amount = self.amount
        if not isinstance(force_amount, bool):
            amount = force_amount
        return float_round(amount, digits)

    def trigger_transaction(self):
        """
        Trigger the transaction steps:
        - Trigger the transaction (depending on your provider)
        - Update the transaction with the response
        - Parse the response (if necessary) to sent it back.
        """
        self.ensure_one()
        if self.return_url and self.return_url != self.return_url.format(
            transaction=self
        ):
            self.write(
                {"return_url": self.return_url.format(transaction=self)}
            )
        data = self._prepare_transaction_data()
        response = self._trigger_transaction_provider(data)
        self._update_with_response(response)
        return self._parse_transaction_response(response)

    def _prepare_transaction_data(self):
        return {}

    def _trigger_transaction_provider(self, data):
        return {}

    def _update_with_response(self, response):
        raise NotImplementedError()

    def _parse_transaction_response(self, response):
        """
        By default, the raw response is returned as is.
        """
        return response
