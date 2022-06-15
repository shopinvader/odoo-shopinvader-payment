# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ast import literal_eval

from odoo.addons.component.core import AbstractComponent


class AbstractPayableSaleService(AbstractComponent):
    _inherit = "shopinvader.abstract.payable.sale.service"

    def _get_available_payment_methods(self, sale):
        payments = super()._get_available_payment_methods(sale)
        return payments.filtered(
            lambda payment: (
                not payment.domain
                or payment.domain == "[]"
                or sale.filtered_domain(literal_eval(payment.domain))
            )
        )
