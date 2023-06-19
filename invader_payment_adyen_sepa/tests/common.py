# Copyright 2023 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from datetime import timedelta

from odoo import fields
from odoo.tests.common import SavepointCase


class TestCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.euro = cls.env.ref("base.EUR")
        company_fr_data = {
            "name": "French company",
            "currency_id": cls.euro.id,
            "country_id": cls.env.ref("base.fr").id,
        }
        cls.company_fr = cls.env["res.company"].create(company_fr_data)
        cls.env.ref("l10n_generic_coa.configurable_chart_template")._load(
            15.0, 15.0, cls.company_fr
        )
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=cls.company_fr.ids,
            )
        )
        cls.AccountPaymentOrder = cls.env["account.payment.order"]
        cls.PaymentAcquirer = cls.env["payment.acquirer"]
        cls.AccountJournal = cls.env["account.journal"]
        cls.PartnerBank = cls.env["res.partner.bank"]
        cls.Mandate = cls.env["account.banking.mandate"]
        cls.PaymentMethod = cls.env["account.payment.method"]
        cls.PaymentMode = cls.env["account.payment.mode"]
        cls.AccountMove = cls.env["account.move"]
        cls.Partner = cls.env["res.partner"]
        cls.AccountAccount = cls.env["account.account"]
        cls.AccountPaymentLineCreate = cls.env["account.payment.line.create"]
        cls.belgium = cls.env.ref("base.be")
        product = cls.env.ref("product.product_product_4").copy()
        product.write({"company_id": cls.company_fr.id})
        cls.acquirer = cls.PaymentAcquirer.create(
            {
                "name": "Shopinvader Adyen - Unit test",
                "provider": "adyen",
                "adyen_hmac_key": "dummy",
                "adyen_checkout_api_url": "dummy",
                "state": "test",
                "view_template_id": cls.env["ir.ui.view"]
                .search([("type", "=", "qweb")], limit=1)
                .id,
                "adyen_live_endpoint_prefix": os.environ.get(
                    "ADYEN_API_PREFIX", "def"
                ),
                "adyen_api_key": os.environ.get("ADYEN_API_KEY", "abc"),
                "adyen_merchant_account": os.environ.get(
                    "ADYEN_MERCHANT_ACCOUNT", "xxx"
                ),
            }
        )
        cls.acquirer.write({"company_id": cls.company_fr.id})
        cls.partner = cls.Partner.create(
            {
                "name": "Test Partner",
                "street": "Main street",
                "city": "Tintigny",
                "country_id": cls.belgium.id,
                "zip": "6730",
            }
        )
        cls.bank = cls.PartnerBank.create(
            {
                "acc_number": "BE68 5390 0754 7034",
                "acc_type": "iban",
                "partner_id": cls.company_fr.partner_id.id,
            }
        )
        cls.bank_partner = cls.PartnerBank.create(
            {
                "acc_number": "FR7630006000011234567890189",
                "acc_type": "iban",
                "partner_id": cls.partner.id,
            }
        )
        cls.mandate = cls.Mandate.create(
            {
                "partner_bank_id": cls.bank_partner.id,
                "signature_date": "2015-01-01",
                "company_id": cls.company_fr.id,
            }
        )
        cls.mandate.validate()
        cls.invoice_line_account = cls.AccountAccount.create(
            {
                "name": "Test account",
                "code": "TEST1",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_expenses"
                ).id,
                "company_id": cls.company_fr.id,
            }
        )
        payment_method_sepa = cls.PaymentMethod.create(
            {
                "name": "SEPA IN",
                "code": "sepa_direct_debit",
                "payment_type": "inbound",
                "bank_account_required": True,
                "mandate_required": True,
                "payment_acquirer_id": cls.acquirer.id,
            }
        )
        cls.journal = cls.AccountJournal.create(
            {
                "name": "SEPA Journal",
                "code": "sepa123",
                "type": "bank",
                "company_id": cls.company_fr.id,
                "bank_account_id": cls.bank.id,
                "outbound_payment_method_ids": [
                    (6, False, payment_method_sepa.ids)
                ],
                "currency_id": cls.euro.id,
            }
        )
        cls.AccountJournal.create(
            {
                "name": "General",
                "code": "general1236",
                "type": "general",
                "company_id": cls.company_fr.id,
                "bank_account_id": cls.bank.id,
                "outbound_payment_method_ids": [
                    (6, False, payment_method_sepa.ids)
                ],
                "currency_id": cls.euro.id,
            }
        )
        cls.payment_mode = cls.PaymentMode.create(
            {
                "name": "test_mode",
                "active": True,
                "payment_method_id": payment_method_sepa.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
            }
        )
        cls.invoice = cls.AccountMove.create(
            {
                "partner_id": cls.partner.id,
                "move_type": "out_invoice",
                "ref": "myref321",
                "payment_mode_id": cls.payment_mode.id,
                "invoice_date": fields.Date.today(),
                "company_id": cls.company_fr.id,
                "currency_id": cls.euro.id,
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "name": "product that cost 100",
                            "account_id": cls.invoice_line_account.id,
                        },
                    )
                ],
            }
        )
        cls.payment_order = cls.AccountPaymentOrder.create(
            {
                "payment_mode_id": cls.payment_mode.id,
                "journal_id": cls.journal.id,
                "date_prefered": "due",
            }
        )

    def _wizard_fill_payment_lines(self, payment_order):
        AccountPaymentLineCreate = self.AccountPaymentLineCreate.with_context(
            active_model=payment_order._name, active_id=payment_order.id
        )
        line_create = AccountPaymentLineCreate.create(
            {
                "date_type": "move",
                "move_date": fields.Datetime.now() + timedelta(days=1),
            }
        )
        line_create.payment_mode = "any"
        line_create.move_line_filters_change()
        line_create.populate()
        line_create.create_payment_lines()
        line_created_due = AccountPaymentLineCreate.create(
            {
                "date_type": "due",
                "due_date": fields.Datetime.now() + timedelta(days=1),
            }
        )
        line_created_due.populate()
        line_created_due.create_payment_lines()
        return True
