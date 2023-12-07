# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import threading

from odoo import SUPERUSER_ID, api, fields, models, registry
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)

try:
    pass
except ImportError as err:
    _logger.debug(err)


class InvaderPayable(models.AbstractModel):
    """
    Abstract class used to execute the payment capture
    """

    _inherit = "invader.payable"
    _description = "Adyen Klarna capture Mixin"

    def _get_klarna_capture_ref(self, transaction):
        reference = transaction.reference
        # Let's possibility to specify a custom reference.
        # Could be useful when you do multi-capture on a same payment.
        if "klarna_capture_force_reference" in self.env.context:
            reference = self.env.context.get("klarna_capture_force_reference")
        return reference

    def _get_klarna_capture_amount(self, transaction):
        amount = transaction.amount
        # In klarna, it's not mandatory to do a full capture.
        # So let's a possibility to specify another amount
        if "klarna_capture_force_amount" in self.env.context:
            amount = self.env.context.get("klarna_capture_force_amount")
        return amount

    def _get_klarna_capture_currency(self, transaction):
        currency = transaction.currency_id
        if not currency:
            company = self.env.company
            if hasattr(self, "company_id") and self.company_id:
                company = self.company_id
            currency = company.currency_id
        return currency

    def _get_klarna_capture_psp(self, transaction):
        return transaction.acquirer_reference

    def _get_klarna_capture_merchant_account(self, transaction):
        return transaction.acquirer_id._get_adyen_merchant_account()

    def _build_klarna_capture_params(self, transaction):
        currency = self._get_klarna_capture_currency(transaction)
        amount = self._get_klarna_capture_amount(transaction)
        return {
            "originalReference": self._get_klarna_capture_psp(transaction),
            "modificationAmount": {
                "value": self._get_formatted_amount(transaction, amount),
                "currency": currency.name,
            },
            "reference": self._get_klarna_capture_ref(transaction),
            "merchantAccount": self._get_klarna_capture_merchant_account(
                transaction
            ),
        }

    def _is_candidate_for_klarna_capture(self, transaction):
        """
        What is check:
        No transaction => Not candidate
        Not adyen provider => Not candidate
        Not klarna in selected payment method => Not candidate
        Transaction already in final state (done, error) => Not candidate
        Amount to capture is 0 => Not candidate
        """
        currency = self._get_klarna_capture_currency(transaction)
        if not transaction:
            _logger.error(
                "Transaction not found for {pay_name}.".format(pay_name=self)
            )
            return False
        elif not transaction.acquirer_id.delay_capture:
            _logger.error(
                "Transaction {tr_name} is not delayed capture".format(
                    tr_name=transaction.display_name
                )
            )
            return False
        # The "klarna" payment method is used to pay later
        # /!\ "klarna" != "klarna_account" etc
        elif "klarna" not in (transaction.adyen_payment_method or ""):
            _logger.error(
                "Transaction {tr_name} doesn't have an klarna payment method.".format(
                    tr_name=transaction.display_name
                )
            )
            return False
        # If the transaction is already into a final state,
        # the capture can't be done.
        elif transaction.state in ("done", "error"):
            _logger.error(
                "Transaction {tr_name} is already into a "
                "final state. Capture cancelled.".format(
                    tr_name=transaction.display_name
                )
            )
            return False
        # Nothing to capture
        elif float_is_zero(
            self._get_klarna_capture_amount(transaction),
            precision_digits=currency.decimal_places or 2,
        ):
            _logger.error(
                "Transaction {tr_name} capture cancelled: amount is 0.".format(
                    tr_name=transaction.display_name
                )
            )
            return False
        return True

    def _do_klarna_capture(self):
        transaction = fields.first(self._invader_get_transactions())
        if self._is_candidate_for_klarna_capture(transaction):
            values = self._build_klarna_capture_params(transaction)
            adyen = transaction._get_service()
            response = adyen.payment.capture(values)
            if (
                response.status_code == 200
                and response.message.get("response") == "[capture-received]"
            ):
                transaction._set_transaction_done()
            else:
                details = response.raw_response
                transaction._set_transaction_error(details)

    def _trigger_klarna_capture(self):
        payable_transactions = {
            record: fields.first(record._invader_get_transactions())
            for record in self
        }
        record_ids = [
            record.id
            for record, transaction in payable_transactions.items()
            if record._is_candidate_for_klarna_capture(transaction)
        ]
        target_model = self._name
        dbname = self.env.cr.dbname
        context = self.env.context.copy()
        description_base = "Execute klarna capture {name}"
        # No commit in test mode so this postcommit doesn't work
        test_mode = getattr(threading.currentThread(), "testing", False)
        if not test_mode:
            # Do it only if the transaction is correctly committed.
            # Then trigger the job to do the capture.
            @self.env.cr.postcommit.add
            def execute_klarna_capture():
                db_registry = registry(dbname)
                with api.Environment.manage(), db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, context)
                    records = env[target_model].browse(record_ids)
                    for record in records:
                        description = description_base.format(
                            name=record.display_name
                        )
                        record.with_delay(
                            description=description
                        )._do_klarna_capture()

        else:
            for record in self.browse(record_ids):
                description = description_base.format(name=record.display_name)
                record.with_delay(description=description)._do_klarna_capture()
