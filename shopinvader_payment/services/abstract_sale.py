# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import AbstractComponent


class AbstractSaleService(AbstractComponent):

    _inherit = "shopinvader.abstract.sale.service"

    def _convert_one_sale(self, sale):
        """
        Add Transaction informations
        :return:
        """
        values = super()._convert_one_sale(sale)
        payment = self.work.component(usage="invader.payment")
        values.update(payment._to_json(sale._invader_get_transactions()))
        return values
