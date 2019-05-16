# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import tools
from odoo.addons.shopinvader.tests.common import CommonCase
from odoo.modules.module import get_module_resource


class CommonCaseShopinvaderInvoice(CommonCase):
    def _load(self, module, *args):
        current_module = "shopinvader_invoice_payment"
        path = get_module_resource(module, *args)
        tools.convert_file(
            self.cr,
            current_module,
            path,
            {},
            "init",
            False,
            "test",
            self.registry._assertion_report,
        )

    def _create_invoice(
        self,
        partner=False,
        company=False,
        journal=False,
        account=False,
        backend=False,
    ):
        """

        :param partner: res.partner recordset
        :param company: res.company recordset
        :param journal: account.journal recordset
        :param account: account.account recordset
        :param backend: shopinvader.backend recordset
        :return: account.invoice recordset
        """
        partner = partner or self.partner
        company = company or self.env.user.company_id
        journal = journal or self.journal
        account = account or self.account_exp
        backend = backend or self.backend
        inv_values = {
            "partner_id": partner.id,
            "company_id": company.id,
            "journal_id": journal.id,
            "state": "draft",
            "type": "out_invoice",
            "account_id": account.id,
            "name": "Shopinvader invoice",
            "shopinvader_backend_id": backend.id,
        }
        return self.invoice_obj.create(inv_values)

    def _create_invoice_line(
        self, invoice=False, product=False, account=False, price_unit=100
    ):
        """

        :param invoice: account.invoice recordset
        :param product: product.product recordset
        :param account: account.account recordset
        :param price_unit:float
        :return: account.invoice.line recordset
        """
        invoice = invoice or self._create_invoice()
        product = product or self.product1
        name = product.display_name or "An invoice line"
        account = account or self.account_pay
        line_values = {
            "invoice_id": invoice.id,
            "name": name,
            "product_id": product.id,
            "price_unit": price_unit,
            "account_id": account.id,
        }
        _new = self.invoice_line_obj.new(line_values)
        _new._onchange_product_id()
        values = _new._convert_to_write(_new._cache)
        values.update(line_values)
        invoice_line = self.invoice_line_obj.create(values)
        return invoice_line

    def setUp(self, *args, **kwargs):
        super(CommonCaseShopinvaderInvoice, self).setUp(*args, **kwargs)
        self._load("account", "test", "account_minimal_test.xml")
        self.partner = self.env.ref("base.res_partner_1")
        self.account_exp = self.env.ref(
            "shopinvader_invoice_payment.a_expense"
        )
        self.account_pay = self.env.ref("shopinvader_invoice_payment.a_pay")
        self.account_payment_mode = self.env.ref(
            "shopinvader_payment.payment_method_check"
        )
        self.journal = self.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )
        self.product1 = self.env.ref("product.product_product_4")
        self.product2 = self.env.ref("product.product_product_5")
        self.invoice_obj = self.env["account.invoice"]
        self.invoice_line_obj = self.env["account.invoice.line"]
        self.invoice = self._create_invoice()
        self._create_invoice_line(self.invoice, product=self.product1)
        self._create_invoice_line(self.invoice, product=self.product2)
        with self.work_on_services(partner=self.partner) as work:
            self.service = work.component(usage="invoice")
