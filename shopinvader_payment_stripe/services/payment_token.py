# Copyright 2020 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentTokenService(Component):
    _inherit = "shopinvader.payment.token.service"

    def _validator_create(self):
        res = super()._validator_create()
        res["stripe_payment_method"] = {"type": "string"}
        return res

    def _json_parser(self):
        res = super()._json_parser()
        res.append("stripe_payment_method")
        return res
