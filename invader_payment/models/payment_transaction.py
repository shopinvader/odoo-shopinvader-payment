# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

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

    @api.model
    def create(self, vals):
        record = super(PaymentTransaction, self).create(vals)
        record._notify_state_changed_event()
        return record

    def write(self, vals):
        res = super(PaymentTransaction, self).write(vals)
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
