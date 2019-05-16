# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class InvoiceService(Component):
    _name = "shopinvader.invoice.service"
    _inherit = [_name, "shopinvader.abstract.payment.service"]

    def _load_target(self, params):
        """

        :param params: dict
        :return: exposed model recordset
        """
        _id = params.get("id")
        return self._get(_id=_id)

    def _validator_add_payment(self):
        schema = super(InvoiceService, self)._validator_add_payment()
        schema.update({"id": {"required": True, "coerce": to_int}})
        return schema

    def _to_json_invoice(self, invoice):
        values = self._convert_one_target(invoice)
        values.update(super(InvoiceService, self)._to_json_invoice(invoice))
        return values
