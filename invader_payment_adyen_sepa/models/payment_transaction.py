# Copyright 2023 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models

from odoo.addons.invader_payment_adyen.services.payment_adyen import (
    ADYEN_TRANSACTION_STATUSES,
)

ADYEN_SEPA_PAYMENT_METHOD = "sepadirectdebit"


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    payment_order_ids = fields.Many2many(
        comodel_name="account.payment.order",
        relation="account_payment_order_transaction_rel",
        column1="transaction_id",
        column2="payment_order_id",
        string="Payment orders",
        copy=False,
        readonly=True,
    )
    payment_order_nbr = fields.Integer(
        compute="_compute_payment_order_nbr", string="# of payment orders"
    )

    payment_order_line_ids = fields.Many2many(
        comodel_name="account.payment.line",
        relation="account_payment_line_transaction_rel",
        column1="transaction_id",
        column2="payment_order_line_id",
        string="Payment orders lines",
        copy=False,
        readonly=True,
    )
    payment_order_line_nbr = fields.Integer(
        compute="_compute_payment_order_line_nbr",
        string="# of payment orders lines",
    )

    def _get_invader_payables(self):
        """
        Inherit to return payment_order_line_ids
        :return: recordset
        """
        self.ensure_one()
        if self.payment_order_line_ids:
            return self.payment_order_line_ids
        return super()._get_invader_payables()

    @api.depends("payment_order_ids")
    def _compute_payment_order_nbr(self):
        """
        Compute function for the field payment_order_nbr.
        Count the number of payment_order_ids.
        :return:
        """
        for record in self:
            record.payment_order_nbr = len(record.payment_order_ids)

    @api.depends("payment_order_ids")
    def _compute_payment_order_line_nbr(self):
        """
        Compute function for the field payment_order_line_nbr.
        Count the number of payment_order_line_ids.
        :return:
        """
        for record in self:
            record.payment_order_line_nbr = len(record.payment_order_line_ids)

    def _prepare_adyen_payments_request(self, payment_method):
        """
        Adyen SEPA payment documentation:
        https://docs.adyen.com/payment-methods/sepa-direct-debit/
        api-only?tab=codeBlocksepa_payments_XpcBC_py_5
        Prepare payments request
        :param payment_method:
        :return:
        """
        request = super()._prepare_adyen_payments_request(payment_method)
        if self.adyen_payment_method == ADYEN_SEPA_PAYMENT_METHOD:
            payable = self._get_invader_payables()
            partner = payable._get_billing_partner()
            partner_bank = payable.partner_bank_id
            if not partner_bank.acc_number:
                raise exceptions.UserError(
                    _(
                        "The partner {partner_name} doesn't have an bank account set."
                    ).format(partner_name=partner.display_name)
                )
            request.update(
                {
                    "paymentMethod": {
                        "type": ADYEN_SEPA_PAYMENT_METHOD,
                        "sepa.ownerName": partner.name or "",
                        "sepa.ibanNumber": partner_bank.acc_number,
                    }
                }
            )
            # Disable ThreeD for SEPA
            add_data = request.get("additionalData", {})
            add_data.update({"executeThreeD": False})
            request.update({"additionalData": add_data})
        return request

    def _trigger_adyen_sepa(self):
        self.ensure_one()
        adyen = self._get_adyen_service()
        request = self._prepare_adyen_payments_request(payment_method={})
        response = adyen.checkout.payments(request)
        self._update_with_adyen_response(response)
        result_code = response.message.get("resultCode")
        if result_code == "Authorised":
            self._set_transaction_done()
        elif result_code == "Received":
            self._set_transaction_authorized()
        else:
            self.write({"state": ADYEN_TRANSACTION_STATUSES[result_code]})

    @api.model
    def _cron_trigger_adyen_sepa(self):
        domain = [
            ("state", "=", "draft"),
            ("adyen_payment_method", "=", ADYEN_SEPA_PAYMENT_METHOD),
        ]
        for transaction in self.search(domain):
            # Create an identity_key to avoid have duplicate jobs on the same transaction
            identity_key = "{model},{id}_trigger_adyen_sepa".format(
                model=transaction._name,
                id=transaction.id,
            )
            description = _("Trigger the SEPA payment on Adyen")
            params = {
                "identity_key": identity_key,
                "description": description,
            }
            transaction.with_delay(**params)._trigger_adyen_sepa()
