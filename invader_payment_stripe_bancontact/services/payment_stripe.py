# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class PaymentServiceStripe(AbstractComponent):

    _inherit = "payment.service.stripe"

    def _get_chargeable_provider(self):
        """
        Overwrite to add providers which use the charge api
        :return: list of str
        """
        res = super()._get_chargeable_provider()
        res.append("stripe_bancontact")
        return res
