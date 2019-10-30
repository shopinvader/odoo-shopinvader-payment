# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.multi
    def write(self, vals):
        res = super(PaymentTransaction, self).write(vals)
        if "state" in vals:
            self._notify_state_changed_event()
        return res

    @api.multi
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

    # CODE BELOW IS A BACKPORT FROM ODOO 12.0 TO HAVE THE SAME API
    # IN odoo-shopinvader-payment 10.0 AND 12.0 !!!!!!!

    @api.model
    def _compute_reference_prefix(self, values):
        if values and values.get("invoice_ids"):
            many_list = self.resolve_2many_commands(
                "invoice_ids", values["invoice_ids"], fields=["number"]
            )
            return ",".join(dic["number"] for dic in many_list)
        return None

    @api.model
    def _compute_reference(self, values=None, prefix=None):
        """Compute a unique reference for the transaction.
        If prefix:
            prefix-d+
        If some invoices:
            <inv_number_0>.number,<inv_number_1>,...,<inv_number_n>-x
        If some sale orders:
            <so_name_0>.number,<so_name_1>,...,<so_name_n>-x
        Else:
            tx-d+
        :param values: values used to create a new transaction.
        :param prefix: custom transaction prefix.
        :return: A unique reference for the transaction.
        """
        if not prefix:
            if values:
                prefix = self._compute_reference_prefix(values)
            else:
                prefix = "tx"

        # Fetch the last reference
        # E.g. If the last reference is SO42-5, this query will return '-5'
        self._cr.execute(
            r"""
            SELECT CAST(SUBSTRING(reference FROM '-\d+$') AS INTEGER) AS suffix
            FROM payment_transaction WHERE reference LIKE %s ORDER BY suffix
            """,  # noqa: W605
            [prefix + "-%"],
        )
        query_res = self._cr.fetchone()
        if query_res:
            # Increment the last reference by one
            suffix = "%s" % (-query_res[0] + 1)
        else:
            # Start a new indexing from 1
            suffix = "1"

        return "{}-{}".format(prefix, suffix)

    @api.multi
    def _log_payment_transaction_sent(self):
        """Log the message saying the transaction has been sent to the remote
        server to be processed by the acquirer.
        """
        for trans in self:
            post_message = trans._get_payment_transaction_sent_message()
            for inv in trans.invoice_ids:
                inv.message_post(body=post_message)

    @api.multi
    def _log_payment_transaction_received(self):
        """Log the message saying a response has been received from the remote
         server and some additional informations like the old/new state, the
        reference of the payment... etc.
        :param old_state:       The state of the transaction before the
                                response.
        :param add_messages:    Optional additional messages to log like the
                                capture status.
        """
        for trans in self.filtered(
            lambda t: t.provider not in ("manual", "transfer")
        ):
            post_message = trans._get_payment_transaction_received_message()
            for inv in trans.invoice_ids:
                inv.message_post(body=post_message)

    @api.multi
    def _set_transaction_pending(self):
        """Move the transaction to the pending state(e.g. Wire Transfer)."""
        if any(trans.state != "draft" for trans in self):
            raise ValidationError(
                _("Only draft transaction can be processed.")
            )

        self.write(
            {"state": "pending", "date_validate": fields.Datetime.now()}
        )
        self._log_payment_transaction_received()

    @api.multi
    def _set_transaction_authorized(self):
        """Move the transaction to the authorized state(e.g. Authorize)."""
        if any(trans.state != "draft" for trans in self):
            raise ValidationError(
                _("Only draft transaction can be authorized.")
            )

        self.write(
            {"state": "authorized", "date_validate": fields.Datetime.now()}
        )
        self._log_payment_transaction_received()

    @api.multi
    def _set_transaction_cancel(self):
        """Move the transaction's payment to the cancel state(e.g. Paypal)."""
        if any(trans.state not in ("draft", "authorized") for trans in self):
            raise ValidationError(
                _("Only draft/authorized transaction can be cancelled.")
            )

        # Cancel the existing payments.
        self.mapped("payment_id").cancel()

        self.write({"state": "cancel", "date_validate": fields.Datetime.now()})
        self._log_payment_transaction_received()

    @api.multi
    def _set_transaction_error(self, msg):
        """Move the transaction to the error state (Third party returning
        error e.g. Paypal)."""
        if any(trans.state != "draft" for trans in self):
            raise ValidationError(
                _("Only draft transaction can be processed.")
            )

        self.write(
            {
                "state": "error",
                "date_validate": fields.Datetime.now(),
                "state_message": msg,
            }
        )

    @api.multi
    def _set_transaction_done(self):
        """Move the transaction's payment to the done state(e.g. Paypal)."""
        if any(
            trans.state not in ("draft", "authorized", "pending")
            for trans in self
        ):
            raise ValidationError(
                _("Only draft/authorized transaction can be posted.")
            )

        self.write({"state": "done", "date_validate": fields.Datetime.now()})
