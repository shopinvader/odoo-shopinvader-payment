# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class AdyenKlarnaCaptureManual(models.TransientModel):
    """
    Tool used to capture manually the amount for Adyen Klarna
    """

    _name = "adyen.klarna.capture.manual"
    _description = "Adyen Klarna capture manual"

    amount = fields.Float(
        help="Amount to capture.\n"
        "(Filled by default with the value found on the transaction)",
        readonly=True,
    )
    reference = fields.Char(
        help="Internal reference.\n"
        "(Filled by default with the reference found on the transaction)",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        """
        Inherit the default get to fill automatically the amount and the reference.
        :param fields_list: list of str
        :return: dict
        """
        result = super().default_get(fields_list)
        record = self._get_target_record()
        transaction = fields.first(record._invader_get_transactions())
        amount = record._get_klarna_capture_amount(transaction)
        reference = record._get_klarna_capture_ref(transaction)
        result.update(
            {
                "amount": amount,
                "reference": reference,
            }
        )
        return result

    def do_capture(self):
        """
        Execute the capture after checking if the record is a candidate for Klarna capture.
        """
        record = self._get_target_record()
        transaction = fields.first(record._invader_get_transactions())
        if not record._is_candidate_for_klarna_capture(transaction):
            raise exceptions.UserError(
                _(
                    f"Your record is not a candidate for Klarna capture.\n"
                    f"Please check the transaction: "
                    f"{transaction.display_name} - {transaction.acquirer_reference}"
                )
            )
        record._trigger_klarna_capture()

    def _get_target_record(self):
        """
        Get the target record (based on context) and check if there is only one record.
        """
        target_model = self.env.context.get("active_model")
        target_ids = self.env.context.get("active_ids")
        target_id = self.env.context.get("active_id")
        record = self.env[target_model].browse(target_ids or target_id)
        if len(record) > 1:
            raise exceptions.UserError(_("Please select only one record."))
        return record
