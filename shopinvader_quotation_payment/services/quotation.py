# -*- coding: utf-8 -*-
# Copyright 2016 Akretion (http://www.akretion.com)
# Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.component.core import Component


class QuotationService(Component):
    _inherit = [
        "shopinvader.abstract.payable.sale.service",
        "shopinvader.quotation.service",
    ]
    _name = "shopinvader.quotation.service"

    def _convert_one_sale(self, sale):
        """
        Add Payment information into cart
        :return:
        """
        values = super(QuotationService, self)._convert_one_sale(sale)
        values.update({"payment": self._get_shopinvader_payment_data(sale)})
        return values
