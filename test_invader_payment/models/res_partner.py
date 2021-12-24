# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = ["invader.payable", "res.partner"]
    _name = "res.partner"

    def _invader_prepare_payment_transaction_data(self, acquirer):
        self.ensure_one()
        vals = {
            "amount": 5,
            "currency_id": self.env.ref("base.EUR").id,
            "partner_id": self.id,
            "acquirer_id": acquirer.id,
            "reference": "Fake",
        }
        return vals
