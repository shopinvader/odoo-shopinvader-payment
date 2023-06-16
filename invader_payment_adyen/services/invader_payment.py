# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class InvaderPaymentService(Component):

    _inherit = "invader.payment.service"

    def _json_parser(self):
        """
        Adds the card payment brand to returned data
        """
        res = super()._json_parser()
        res.append("adyen_payment_method")
        return res
